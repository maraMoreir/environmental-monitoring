# Environmental Monitoring with Python and IoT

This project is a solution for environmental monitoring using IoT sensors and cloud data analysis. The goal is to create a system that collects environmental data, stores it in the cloud, and provides insights through interactive dashboards.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)

## Overview

This project uses IoT sensors to monitor environmental variables such as temperature, humidity, and air quality. The data is sent to the cloud, where it is analyzed and visualized through an interactive dashboard.

## Features

- Real-time environmental data collection using IoT sensors.
- Data storage and processing in the cloud.
- Visualization of data through an interactive dashboard.
- Real-time notifications based on specific conditions.

## Requirements

- Python 3.x
- `requests` library for API communication.
- `pandas` library for data manipulation.
- `matplotlib` library for data visualization.
- Other dependencies specified in `requirements.txt`.

## Installation

Follow the steps below to set up the environment and install the project's dependencies:

1. **Clone the repository:**

    ```bash
    git clone https://github.com/maraMoreir/environmental-monitoring.git
    cd environmental-monitoring
    ```

2. **Create and activate a virtual environment:**

    ```bash
    python -m venv env
    source env/bin/activate  # On Windows use `.\env\Scripts\activate`
    ```

3. **Install the dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

## Usage

1. **Sensor Configuration:**

   Configure your IoT sensors according to the manufacturer's instructions. Ensure they are connected and sending data correctly.

2. **Environment Setup:**

   Update the `config.py` file with your cloud and API credentials and settings.

3. **Run the Code:**

    ```bash
    python monitoring.py
    ```

4. **Access the Dashboard:**

   After running the code, you can access the dashboard at [http://localhost:8000](http://localhost:8000) to view the real-time data.

## Project Structure

environmental-monitoring/
├── env/                   
│   └── ...              
├── src/                
│   ├── monitoring.py   
│   ├── config.py           
│   ├── sensors/           
│   │   └── ...            
│   └── dashboard/   
│       └── ...           
├── requirements.txt  
└── README.md               
