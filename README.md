# AQI Reflex Agent

A scalable, modular Air Quality Index agent built in Python.
Implements the India CPCB AQI breakpoint formula and is designed
to grow in complexity as the course progresses.

---

## Members

| Name                  | Roll Number   |
|-----------------------|---------------|
| Pali Krishna Harshith | SE24UCSE001   |
| Abhijit  Jillellamudi | SE24UCSE018   |
| Mayank Rao Ponnala    | SE24UCSE026   |
| Kamal Kumar Nampally  | SE24UCSE110   |

---

## Architecture

### System Overview

```
+------------------------------------------------------------------+
|                         ENVIRONMENT                              |
|                      (environment.py)                            |
|                                                                  |
|   +------------------+          +----------------------------+   |
|   |     SENSOR       |          |          AGENT             |   |
|   |  sensors/        |  ------> |  agents/                   |   |
|   |  base.py         | percept  |  base.py                   |   |
|   |  csv_sensor.py   |          |  simple_reflex.py          |   |
|   +------------------+          |  model_based.py            |   |
|                                 +------------+---------------+   |
|                                              |                   |
|                                           action                 |
|                                              |                   |
|                                 +------------v---------------+   |
|                                 |         PLUGINS            |   |
|                                 |  plugins/                  |   |
|                                 |  logger.py                 |   |
|                                 |  threshold_alert.py        |   |
|                                 +----------------------------+   |
+------------------------------------------------------------------+
```

### Agent Decision Flow

```
  CSV File
     |
     v
+----+----------+
|    SENSOR     |   reads raw rows from city_day.csv
|  csv_sensor   |   maps column aliases to pollutant names
+----+----------+
     |
     |  sensor_data dict
     v
+----+----------+
|   PERCEIVE    |   strips metadata keys
|  agent layer  |   returns clean pollutant readings
+----+----------+
     |
     |  percept dict
     v
+----+--------------+
|  aqi_calculator   |   applies CPCB breakpoint formula per pollutant
|                   |   sub_index(pollutant, concentration)
|  Formula:         |
|  AQI = (AQI_hi - AQI_lo) / (BP_hi - BP_lo)
|      * (Conc - BP_lo) + AQI_lo
+----+--------------+
     |
     |  sub_indices dict
     v
+----+----------+
|     ACT       |   picks dominant (max) sub-index as final AQI
|  agent layer  |   matches AQI to condition-action rule
|               |   returns category + advisory
+----+----------+
     |
     |  action dict
     v
+----+----------+
|   PLUGINS     |   LoggerPlugin      -> writes to output/aqi_log.csv
|               |   ThresholdAlert   -> flags AQI above set limit
+----+----------+
     |
     v
  Output: AQI value, category, dominant pollutant, advisory
```

### Project Structure

```
aqi-reflex-agent/
|
+-- main.py                  Entry point and CLI
+-- aqi_calculator.py        Breakpoint formula (reads config)
+-- environment.py           Agent-sensor-plugin loop
+-- visualizer.py            All chart generation
|
+-- config/
|   +-- pollutants.py        Single source of truth for all breakpoints,
|                            categories, units, and column aliases
|
+-- agents/
|   +-- base.py              Abstract BaseAgent  (perceive / act / run)
|   +-- simple_reflex.py     No memory, pure condition-action rules
|   +-- model_based.py       Keeps history window, detects AQI trend
|
+-- sensors/
|   +-- base.py              Abstract BaseSensor  (read / read_all)
|   +-- csv_sensor.py        Reads from Kaggle CSV files
|
+-- plugins/
|   +-- base.py              Abstract BasePlugin  (process)
|   +-- logger.py            Appends every result to a CSV log
|   +-- threshold_alert.py   Flags observations above a threshold
|
+-- data/
|   +-- city_day.csv         Dataset (Kaggle: rohanrao/air-quality-data-in-india)
|
+-- output/                  Generated charts and logs (runtime, not in repo)
```

---

## How It Is Built for Scalability

### 1. Config is separated from logic

All breakpoints, AQI bins, units, and column aliases live in `config/pollutants.py`.
To add a new pollutant, add one entry there. Nothing else changes.

### 2. Agents share a common interface

Every agent inherits from `agents/base.py` which defines `perceive`, `act`, and `run`.
Switching agents requires only one flag on the command line.

| Agent         | File                    | Description                            |
|---------------|-------------------------|----------------------------------------|
| SimpleReflex  | agents/simple_reflex.py | No memory. Rules on current percept.   |
| ModelBased    | agents/model_based.py   | Keeps history window. Detects trend.   |
| GoalBased     | (add when needed)       | Add agents/goal_based.py               |
| UtilityBased  | (add when needed)       | Add agents/utility_based.py            |
| Learning      | (add when needed)       | Add agents/learning_agent.py           |

### 3. Sensors share a common interface

Every sensor inherits from `sensors/base.py` which defines `read` and `read_all`.
To add a new data source, create a new file in `sensors/` and pass it to `Environment`.

| Sensor       | File                  | Description                     |
|--------------|-----------------------|---------------------------------|
| CSVSensor    | sensors/csv_sensor.py | Reads from Kaggle CSV files     |
| APISensor    | (add when needed)     | Add sensors/api_sensor.py       |
| StreamSensor | (add when needed)     | Add sensors/stream_sensor.py    |

### 4. Plugins extend behavior without touching core logic

Plugins attach to `Environment` and run after every agent decision.
To add new behavior, create a file in `plugins/`, inherit `BasePlugin`, implement `process`.

| Plugin         | File                       | Description                         |
|----------------|----------------------------|-------------------------------------|
| Logger         | plugins/logger.py          | Appends every result to a CSV log   |
| ThresholdAlert | plugins/threshold_alert.py | Flags observations above threshold  |
| Notification   | (add when needed)          | Add plugins/notification.py         |
| Exporter       | (add when needed)          | Add plugins/json_exporter.py        |

### 5. Environment ties everything together

`environment.py` owns the agent-sensor-plugin loop.
Swapping any component requires one line change.

```python
env = Environment(
    sensor  = CSVSensor(),
    source  = "data/city_day.csv",
    plugins = [LoggerPlugin(), ThresholdAlertPlugin(threshold=200)],
)
results = env.run_all(agent)
```

---

## AQI Formula

```
AQI = ((AQI_hi - AQI_lo) / (BP_hi - BP_lo)) * (Conc - BP_lo) + AQI_lo
```

| Symbol  | Meaning                           |
|---------|-----------------------------------|
| Conc    | Measured pollutant concentration  |
| BP_lo   | Lower breakpoint concentration    |
| BP_hi   | Upper breakpoint concentration    |
| AQI_lo  | AQI value corresponding to BP_lo  |
| AQI_hi  | AQI value corresponding to BP_hi  |

Final AQI = sub-index of the dominant (worst) pollutant across all readings.
Source: India CPCB / SIM-air Working Paper Series #46-2021

---

## AQI Categories

| Range    | Category     | Health Implication                                  |
|----------|--------------|-----------------------------------------------------|
| 0-50     | Good         | Minimal impact                                      |
| 51-100   | Satisfactory | Minor discomfort for sensitive individuals          |
| 101-200  | Moderate     | Discomfort for people with lung or heart disease    |
| 201-300  | Poor         | Respiratory illness on prolonged exposure           |
| 301-400  | Very Poor    | Respiratory effects even on light physical activity |
| 401-500  | Severe       | Serious aggravation, affects healthy people too     |

---

## Supported Pollutants

| Pollutant | Unit   | Averaging Period |
|-----------|--------|-----------------|
| PM2.5     | ug/m3  | 24-hour          |
| PM10      | ug/m3  | 24-hour          |
| NO2       | ug/m3  | 24-hour          |
| SO2       | ug/m3  | 24-hour          |
| CO        | mg/m3  | 8-hour           |
| O3        | ug/m3  | 8-hour           |
| NH3       | ug/m3  | 24-hour          |
| Pb        | ug/m3  | 24-hour          |

---

## Setup

```bash
pip install pandas matplotlib numpy
```

---

## Usage

```bash
# Latest row, simple reflex agent
python main.py

# Specific row by index
python main.py --row 5

# All rows with summary table
python main.py --all

# Model-based agent (tracks trend)
python main.py --all --agent model

# Generate charts
python main.py --all --visualize

# Log results to CSV
python main.py --all --log

# Flag observations above AQI 200
python main.py --all --alert 200

# Everything on
python main.py --all --agent model --visualize --log --alert 200

# Use your own dataset
python main.py --file path/to/data.csv --all --visualize
```

---

## Upgrading the Agent as the Course Progresses

```
Week 1  Simple Reflex Agent   python main.py --agent simple
        No memory. Acts on current sensor reading only.

Week 2  Model-Based Agent     python main.py --agent model
        Keeps a rolling history window. Detects worsening or improving trend.

Week 3+ Add a new agent type
        1. Create agents/goal_based.py
        2. Inherit from BaseAgent
        3. Implement perceive() and act()
        4. Add the name to --agent choices in main.py
        No other files need to change.
```

---

## References

- Guttikunda, S. (2021). 10 Frequently Asked Questions on Air Quality Index.
  SIM-air Working Paper Series #46-2021. UrbanEmissions.info
- CPCB (2014). National Air Quality Index. Central Pollution Control Board, India.
- rohanrao (2020). Calculating AQI - Air Quality Index Tutorial. Kaggle.
- Russell, S. & Norvig, P. Artificial Intelligence: A Modern Approach. Chapter 2.
