"""
Módulo de Autenticación de Usuario Completa
Implementa registro, login, gestión de sesiones, recuperación de contraseña y perfiles de usuario
"""

from flask import Blueprint, jsonify, request, session
import hashlib
import secrets
import re
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass, asdict
from typing import Dict, Optional
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

auth_bp = Blueprint('auth', __name__)

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class User:
    """Clase para representar un usuario"""
    user_id: str
    username: str
    email: str
    password_hash: str
    first_name: str
    last_name: str
    phone: str
    risk_profile: str  # 'conservative', 'moderate', 'aggressive'
    investment_experience: str  # 'beginner', 'intermediate', 'advanced'
    initial_capital: float
    created_at: str
    last_login: str
    is_active: bool
    email_verified: bool

@dataclass
class Session:
    """Clase para representar una sesión"""
    session_id: str
    user_id: str
    created_at: str
    expires_at: str
    ip_address: str
    user_agent: str

class AuthenticationManager:
    def __init__(self):
        self.users = {}  # {user_id: User}
        self.sessions = {}  # {session_id: Session}
        self.password_reset_tokens = {}  # {token: user_id}
        self.email_verification_tokens = {}  # {token: user_id}
        
        # Configuración de seguridad
        self.session_duration = timedelta(hours=24)
        self.password_reset_duration = timedelta(hours=1)
        self.min_password_length = 8
        
        # Crear usuarios demo
        self._create_demo_users()
    
    def _create_demo_users(self):
        """Crea usuarios demo para pruebas"""
        demo_users = [
            {
                'username': 'demo',
                'email': 'demo@example.com',
                'password': 'Demo123!',
                'first_name': 'Usuario',
                'last_name': 'Demo',
                'phone': '+1234567890',
                'risk_profile': 'moderate',
                'investment_experience': 'intermediate',
                'initial_capital': 10000.0
            },
            {
                'username': 'admin',
                'email': 'admin@example.com',
                'password': 'Admin123!',
                'first_name': 'Administrador',
                'last_name': 'Sistema',
                'phone': '+1234567891',
                'risk_profile': 'aggressive',
                'investment_experience': 'advanced',
                'initial_capital': 50000.0
            },
            {
                'username': 'investor1',
                'email': 'investor1@example.com',
                'password': 'Investor123!',
                'first_name': 'Juan',
                'last_name': 'Pérez',
                'phone': '+1234567892',
                'risk_profile': 'conservative',
                'investment_experience': 'beginner',
                'initial_capital': 5000.0
            }
        ]
        
        for user_data in demo_users:
            self.register_user(
                username=user_data['username'],
                email=user_data['email'],
                password=user_data['password'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                phone=user_data['phone'],
                risk_profile=user_data['risk_profile'],
                investment_experience=user_data['investment_experience'],
                initial_capital=user_data['initial_capital']
            )
            
            # Verificar email automáticamente para usuarios demo
            user_id = self._get_user_id_by_username(user_data['username'])
            if user_id and user_id in self.users:
                self.users[user_id].email_verified = True
    
    def _hash_password(self, password: str) -> str:
        """Genera hash seguro de la contraseña"""
        salt = secrets.token_hex(16)
        password_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return f"{salt}:{password_hash.hex()}"
    
    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verifica la contraseña contra el hash"""
        try:
            salt, stored_hash = password_hash.split(':')
            password_hash_check = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
            return stored_hash == password_hash_check.hex()
        except Exception:
            return False
    
    def _validate_password(self, password: str) -> Dict:
        """Valida la fortaleza de la contraseña"""
        errors = []
        
        if len(password) < self.min_password_length:
            errors.append(f"La contraseña debe tener al menos {self.min_password_length} caracteres")
        
        if not re.search(r'[A-Z]', password):
            errors.append("La contraseña debe contener al menos una letra mayúscula")
        
        if not re.search(r'[a-z]', password):
            errors.append("La contraseña debe contener al menos una letra minúscula")
        
        if not re.search(r'\d', password):
            errors.append("La contraseña debe contener al menos un número")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("La contraseña debe contener al menos un carácter especial")
        
        return {'valid': len(errors) == 0, 'errors': errors}
    
    def _validate_email(self, email: str) -> bool:
        """Valida el formato del email"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _generate_user_id(self) -> str:
        """Genera un ID único para el usuario"""
        return f"user_{secrets.token_hex(8)}"
    
    def _generate_session_id(self) -> str:
        """Genera un ID único para la sesión"""
        return f"session_{secrets.token_hex(16)}"
    
    def _get_user_id_by_username(self, username: str) -> Optional[str]:
        """Obtiene el user_id por username"""
        for user_id, user in self.users.items():
            if user.username == username:
                return user_id
        return None
    
    def _get_user_id_by_email(self, email: str) -> Optional[str]:
        """Obtiene el user_id por email"""
        for user_id, user in self.users.items():
            if user.email == email:
                return user_id
        return None
    
    def register_user(self, username: str, email: str, password: str, 
                     first_name: str, last_name: str, phone: str = "",
                     risk_profile: str = "moderate", investment_experience: str = "beginner",
                     initial_capital: float = 10000.0) -> Dict:
        """
        Registra un nuevo usuario
        """
        try:
            # Validaciones
            if not username or len(username) < 3:
                return {'error': 'El nombre de usuario debe tener al menos 3 caracteres'}
            
            if not self._validate_email(email):
                return {'error': 'Formato de email inválido'}
            
            password_validation = self._validate_password(password)
            if not password_validation['valid']:
                return {'error': 'Contraseña inválida', 'details': password_validation['errors']}
            
            # Verificar si el usuario ya existe
            if self._get_user_id_by_username(username):
                return {'error': 'El nombre de usuario ya existe'}
            
            if self._get_user_id_by_email(email):
                return {'error': 'El email ya está registrado'}
            
            # Crear usuario
            user_id = self._generate_user_id()
            password_hash = self._hash_password(password)
            
            user = User(
                user_id=user_id,
                username=username,
                email=email,
                password_hash=password_hash,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                risk_profile=risk_profile,
                investment_experience=investment_experience,
                initial_capital=initial_capital,
                created_at=datetime.now().isoformat(),
                last_login="",
                is_active=True,
                email_verified=False
            )
            
            self.users[user_id] = user
            
            # Generar token de verificación de email
            verification_token = secrets.token_urlsafe(32)
            self.email_verification_tokens[verification_token] = user_id
            
            logger.info(f"Usuario registrado: {username} ({email})")
            
            return {
                'success': True,
                'user_id': user_id,
                'message': 'Usuario registrado exitosamente',
                'verification_token': verification_token  # En producción, esto se enviaría por email
            }
            
        except Exception as e:
            logger.error(f"Error registrando usuario: {str(e)}")
            return {'error': str(e)}
    
    def login_user(self, username: str, password: str, ip_address: str = "", 
                  user_agent: str = "") -> Dict:
        """
        Autentica un usuario y crea una sesión
        """
        try:
            # Buscar usuario
            user_id = self._get_user_id_by_username(username)
            if not user_id:
                # También intentar con email
                user_id = self._get_user_id_by_email(username)
            
            if not user_id or user_id not in self.users:
                return {'error': 'Usuario o contraseña incorrectos'}
            
            user = self.users[user_id]
            
            # Verificar contraseña
            if not self._verify_password(password, user.password_hash):
                return {'error': 'Usuario o contraseña incorrectos'}
            
            # Verificar si el usuario está activo
            if not user.is_active:
                return {'error': 'Cuenta desactivada'}
            
            # Crear sesión
            session_id = self._generate_session_id()
            expires_at = datetime.now() + self.session_duration
            
            session = Session(
                session_id=session_id,
                user_id=user_id,
                created_at=datetime.now().isoformat(),
                expires_at=expires_at.isoformat(),
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            self.sessions[session_id] = session
            
            # Actualizar último login
            user.last_login = datetime.now().isoformat()
            
            logger.info(f"Usuario autenticado: {username}")
            
            return {
                'success': True,
                'session_id': session_id,
                'user_info': {
                    'user_id': user_id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'risk_profile': user.risk_profile,
                    'investment_experience': user.investment_experience,
                    'email_verified': user.email_verified
                },
                'expires_at': expires_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error en login: {str(e)}")
            return {'error': str(e)}
    
    def logout_user(self, session_id: str) -> Dict:
        """
        Cierra la sesión de un usuario
        """
        try:
            if session_id in self.sessions:
                del self.sessions[session_id]
                logger.info(f"Sesión cerrada: {session_id}")
                return {'success': True, 'message': 'Sesión cerrada exitosamente'}
            else:
                return {'error': 'Sesión no encontrada'}
                
        except Exception as e:
            logger.error(f"Error en logout: {str(e)}")
            return {'error': str(e)}
    
    def validate_session(self, session_id: str) -> Dict:
        """
        Valida una sesión activa
        """
        try:
            if session_id not in self.sessions:
                return {'valid': False, 'error': 'Sesión no encontrada'}
            
            session = self.sessions[session_id]
            expires_at = datetime.fromisoformat(session.expires_at)
            
            if datetime.now() > expires_at:
                del self.sessions[session_id]
                return {'valid': False, 'error': 'Sesión expirada'}
            
            user = self.users.get(session.user_id)
            if not user or not user.is_active:
                return {'valid': False, 'error': 'Usuario inactivo'}
            
            return {
                'valid': True,
                'user_info': {
                    'user_id': user.user_id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'risk_profile': user.risk_profile,
                    'investment_experience': user.investment_experience
                }
            }
            
        except Exception as e:
            logger.error(f"Error validando sesión: {str(e)}")
            return {'valid': False, 'error': str(e)}
    
    def request_password_reset(self, email: str) -> Dict:
        """
        Solicita restablecimiento de contraseña
        """
        try:
            user_id = self._get_user_id_by_email(email)
            if not user_id:
                # Por seguridad, no revelamos si el email existe
                return {'success': True, 'message': 'Si el email existe, recibirás instrucciones'}
            
            # Generar token de restablecimiento
            reset_token = secrets.token_urlsafe(32)
            self.password_reset_tokens[reset_token] = {
                'user_id': user_id,
                'expires_at': (datetime.now() + self.password_reset_duration).isoformat()
            }
            
            logger.info(f"Solicitud de restablecimiento de contraseña para: {email}")
            
            return {
                'success': True,
                'message': 'Si el email existe, recibirás instrucciones',
                'reset_token': reset_token  # En producción, esto se enviaría por email
            }
            
        except Exception as e:
            logger.error(f"Error solicitando restablecimiento: {str(e)}")
            return {'error': str(e)}
    
    def reset_password(self, reset_token: str, new_password: str) -> Dict:
        """
        Restablece la contraseña usando un token
        """
        try:
            if reset_token not in self.password_reset_tokens:
                return {'error': 'Token de restablecimiento inválido'}
            
            token_data = self.password_reset_tokens[reset_token]
            expires_at = datetime.fromisoformat(token_data['expires_at'])
            
            if datetime.now() > expires_at:
                del self.password_reset_tokens[reset_token]
                return {'error': 'Token de restablecimiento expirado'}
            
            # Validar nueva contraseña
            password_validation = self._validate_password(new_password)
            if not password_validation['valid']:
                return {'error': 'Contraseña inválida', 'details': password_validation['errors']}
            
            # Actualizar contraseña
            user_id = token_data['user_id']
            if user_id in self.users:
                self.users[user_id].password_hash = self._hash_password(new_password)
                
                # Eliminar token usado
                del self.password_reset_tokens[reset_token]
                
                # Cerrar todas las sesiones del usuario
                sessions_to_remove = [sid for sid, session in self.sessions.items() 
                                    if session.user_id == user_id]
                for sid in sessions_to_remove:
                    del self.sessions[sid]
                
                logger.info(f"Contraseña restablecida para usuario: {user_id}")
                
                return {'success': True, 'message': 'Contraseña restablecida exitosamente'}
            else:
                return {'error': 'Usuario no encontrado'}
                
        except Exception as e:
            logger.error(f"Error restableciendo contraseña: {str(e)}")
            return {'error': str(e)}
    
    def verify_email(self, verification_token: str) -> Dict:
        """
        Verifica el email usando un token
        """
        try:
            if verification_token not in self.email_verification_tokens:
                return {'error': 'Token de verificación inválido'}
            
            user_id = self.email_verification_tokens[verification_token]
            
            if user_id in self.users:
                self.users[user_id].email_verified = True
                del self.email_verification_tokens[verification_token]
                
                logger.info(f"Email verificado para usuario: {user_id}")
                
                return {'success': True, 'message': 'Email verificado exitosamente'}
            else:
                return {'error': 'Usuario no encontrado'}
                
        except Exception as e:
            logger.error(f"Error verificando email: {str(e)}")
            return {'error': str(e)}
    
    def update_user_profile(self, user_id: str, profile_data: Dict) -> Dict:
        """
        Actualiza el perfil del usuario
        """
        try:
            if user_id not in self.users:
                return {'error': 'Usuario no encontrado'}
            
            user = self.users[user_id]
            
            # Campos actualizables
            updatable_fields = ['first_name', 'last_name', 'phone', 'risk_profile', 
                              'investment_experience', 'initial_capital']
            
            for field, value in profile_data.items():
                if field in updatable_fields:
                    setattr(user, field, value)
            
            logger.info(f"Perfil actualizado para usuario: {user_id}")
            
            return {'success': True, 'message': 'Perfil actualizado exitosamente'}
            
        except Exception as e:
            logger.error(f"Error actualizando perfil: {str(e)}")
            return {'error': str(e)}
    
    def get_user_profile(self, user_id: str) -> Dict:
        """
        Obtiene el perfil completo del usuario
        """
        try:
            if user_id not in self.users:
                return {'error': 'Usuario no encontrado'}
            
            user = self.users[user_id]
            
            return {
                'success': True,
                'profile': {
                    'user_id': user.user_id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'phone': user.phone,
                    'risk_profile': user.risk_profile,
                    'investment_experience': user.investment_experience,
                    'initial_capital': user.initial_capital,
                    'created_at': user.created_at,
                    'last_login': user.last_login,
                    'email_verified': user.email_verified
                }
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo perfil: {str(e)}")
            return {'error': str(e)}

# Instancia global del gestor de autenticación
auth_manager = AuthenticationManager()

@auth_bp.route('/auth/register', methods=['POST'])
def register():
    """
    Endpoint para registro de usuarios
    """
    try:
        data = request.get_json()
        
        required_fields = ['username', 'email', 'password', 'first_name', 'last_name']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Campo requerido: {field}'}), 400
        
        result = auth_manager.register_user(
            username=data['username'],
            email=data['email'],
            password=data['password'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            phone=data.get('phone', ''),
            risk_profile=data.get('risk_profile', 'moderate'),
            investment_experience=data.get('investment_experience', 'beginner'),
            initial_capital=data.get('initial_capital', 10000.0)
        )
        
        if 'error' in result:
            return jsonify(result), 400
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error en endpoint register: {str(e)}")
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/auth/login', methods=['POST'])
def login():
    """
    Endpoint para login de usuarios
    """
    try:
        data = request.get_json()
        
        if 'username' not in data or 'password' not in data:
            return jsonify({'error': 'Se requieren username y password'}), 400
        
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent', '')
        
        result = auth_manager.login_user(
            username=data['username'],
            password=data['password'],
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        if 'error' in result:
            return jsonify(result), 401
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error en endpoint login: {str(e)}")
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/auth/logout', methods=['POST'])
def logout():
    """
    Endpoint para logout de usuarios
    """
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        
        if not session_id:
            return jsonify({'error': 'Se requiere session_id'}), 400
        
        result = auth_manager.logout_user(session_id)
        
        if 'error' in result:
            return jsonify(result), 400
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error en endpoint logout: {str(e)}")
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/auth/validate-session', methods=['POST'])
def validate_session():
    """
    Endpoint para validar sesión
    """
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        
        if not session_id:
            return jsonify({'error': 'Se requiere session_id'}), 400
        
        result = auth_manager.validate_session(session_id)
        
        if not result.get('valid', False):
            return jsonify(result), 401
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error en endpoint validate_session: {str(e)}")
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/auth/request-password-reset', methods=['POST'])
def request_password_reset():
    """
    Endpoint para solicitar restablecimiento de contraseña
    """
    try:
        data = request.get_json()
        
        if 'email' not in data:
            return jsonify({'error': 'Se requiere email'}), 400
        
        result = auth_manager.request_password_reset(data['email'])
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error en endpoint request_password_reset: {str(e)}")
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/auth/reset-password', methods=['POST'])
def reset_password():
    """
    Endpoint para restablecer contraseña
    """
    try:
        data = request.get_json()
        
        if 'reset_token' not in data or 'new_password' not in data:
            return jsonify({'error': 'Se requieren reset_token y new_password'}), 400
        
        result = auth_manager.reset_password(data['reset_token'], data['new_password'])
        
        if 'error' in result:
            return jsonify(result), 400
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error en endpoint reset_password: {str(e)}")
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/auth/verify-email', methods=['POST'])
def verify_email():
    """
    Endpoint para verificar email
    """
    try:
        data = request.get_json()
        
        if 'verification_token' not in data:
            return jsonify({'error': 'Se requiere verification_token'}), 400
        
        result = auth_manager.verify_email(data['verification_token'])
        
        if 'error' in result:
            return jsonify(result), 400
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error en endpoint verify_email: {str(e)}")
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/auth/profile/<user_id>', methods=['GET'])
def get_profile(user_id):
    """
    Endpoint para obtener perfil de usuario
    """
    try:
        result = auth_manager.get_user_profile(user_id)
        
        if 'error' in result:
            return jsonify(result), 404
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error en endpoint get_profile: {str(e)}")
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/auth/profile/<user_id>', methods=['PUT'])
def update_profile(user_id):
    """
    Endpoint para actualizar perfil de usuario
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Se requieren datos para actualizar'}), 400
        
        result = auth_manager.update_user_profile(user_id, data)
        
        if 'error' in result:
            return jsonify(result), 400
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error en endpoint update_profile: {str(e)}")
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/auth/users', methods=['GET'])
def list_users():
    """
    Endpoint para listar usuarios (solo para admin)
    """
    try:
        users_list = []
        for user_id, user in auth_manager.users.items():
            users_list.append({
                'user_id': user.user_id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'risk_profile': user.risk_profile,
                'investment_experience': user.investment_experience,
                'created_at': user.created_at,
                'last_login': user.last_login,
                'is_active': user.is_active,
                'email_verified': user.email_verified
            })
        
        return jsonify({
            'success': True,
            'users': users_list,
            'total_users': len(users_list)
        })
        
    except Exception as e:
        logger.error(f"Error en endpoint list_users: {str(e)}")
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/auth/health', methods=['GET'])
def auth_health_check():
    """
    Endpoint para verificar el estado del módulo de autenticación
    """
    return jsonify({
        'success': True,
        'status': 'healthy',
        'total_users': len(auth_manager.users),
        'active_sessions': len(auth_manager.sessions),
        'pending_password_resets': len(auth_manager.password_reset_tokens),
        'pending_email_verifications': len(auth_manager.email_verification_tokens),
        'timestamp': datetime.now().isoformat()
    })

