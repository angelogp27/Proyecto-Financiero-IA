# Proyecto-Financiero-IA

Este proyecto está diseñado para integrar modelos de **predicción de mercado** utilizando **SVM** (Support Vector Machine), **LSTM** (Long Short-Term Memory), y **análisis de noticias**. Además, se implementa un módulo de **estrategias de inversión** y **backtesting** para evaluar el rendimiento de las estrategias generadas. 

Ingresa desde: https://mhomvbnv.manus.space/

## Descripción General

El sistema permite generar predicciones de precios y señales de trading utilizando datos históricos y diversas fuentes de información. Las señales generadas se combinan para formar recomendaciones de inversión que luego se evaluarán mediante un proceso de backtesting.

### Componentes del Proyecto:

1. **Predicciones con SVM y LSTM:** 
   - Predicción de subidas y bajadas en el mercado mediante el modelo SVM.
   - Pronóstico de precios futuros con el modelo LSTM.
   
2. **Estrategias de Inversión:** 
   - Creación de estrategias de inversión basadas en las señales generadas.
   - Implementación de diferentes tipos de estrategias: **conservadora**, **moderada** y **agresiva**.

3. **Backtesting:** 
   - Evaluación de la efectividad de las estrategias con datos históricos.
   - Cálculo de métricas de rendimiento como el **retorno total**, **índice de Sharpe** y **máximo drawdown**.

4. **Análisis de Noticias:** 
   - Integración de noticias financieras mediante análisis de sentimiento y detección de eventos clave.

## Integrantes del Grupo

### 1. **Angelo Diego Goitia Peves**  
   - Rol: **Líder del Proyecto**  
### 2. **Pedro Fernando Yanyachi Perez**  
### 3. **Josue Martines Cancho**
### 4. **Piero Carlinho Vargas Chota** 
### 5. **Elizabeth Xiomara Coronado Lucano**  

### Mención honorífica: **Clarissa Regina Magan Muñoz**  
   
## Tecnologías Utilizadas

- **Backend:** Python, Flask, Scikit-learn, TensorFlow
- **Frontend:** React, Tailwind CSS, Lucide Icons
- **Base de Datos:** MySQL / PostgreSQL
- **Modelos de Predicción:** SVM, LSTM
- **Análisis de Sentimiento:** TextBlob, NLTK
- **Visualización:** Chart.js (para gráficos de predicción)
  
## Instalación

1. Clonar el repositorio:

    ```bash
    git clone https://github.com/usuario/proyecto-predicciones.git
    cd proyecto-predicciones
    ```

2. Crear un entorno virtual (opcional pero recomendado):

    ```bash
    python3 -m venv venv
    source venv/bin/activate  # En Windows: venv\Scripts\activate
    ```

3. Instalar las dependencias:

    ```bash
    pip install -r requirements.txt
    ```

4. Ejecutar el servidor Flask:

    ```bash
    python app.py
    ```

5. Acceder al frontend en el navegador:

    ```bash
    npm start
    ```

## Contribuciones

Si deseas contribuir a este proyecto, por favor realiza un fork del repositorio y envía un **pull request** con tus cambios. Para contribuir, asegúrate de seguir estas normas:

1. Asegúrate de que tu código esté bien documentado.
2. Realiza pruebas adecuadas para validar tus cambios.
3. Asegúrate de que el código siga el estilo del proyecto.


