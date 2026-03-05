# AQI Reflex Agent

A scalable, modular Air Quality Index agent built in Python.
Implements the India CPCB AQI breakpoint formula and is designed
to grow in complexity as the course progresses.

---

## Architecture

```
aqi-reflex-agent/
    main.py                     Entry point and CLI
    aqi_calculator.py           Breakpoint formula (reads from config)
    environment.py              Agent-sensor-plugin loop
    visualizer.py               All chart generation
    |
    config/
        pollutants.py           Single source of truth for all breakpoints,
                                categories, units, and column aliases.
                                Add a new pollutant here and it works everywhere.
    agents/
        base.py                 Abstract BaseAgent (perceive / act / run)
        simple_reflex.py        Week 1: condition-action rules, no memory
        model_based.py          Week 2+: adds internal state, trend detection
    sensors/
        base.py                 Abstract BaseSensor (read / read_all)
        csv_sensor.py           Reads from CSV files (Kaggle dataset)
    plugins/
        base.py                 Abstract BasePlugin (process)
        logger.py               Writes every result to a CSV log file
        threshold_alert.py      Raises alerts when AQI exceeds a threshold
    data/
        city_day.csv            Dataset from Kaggle (rohanrao/air-quality-data-in-india)
    output/                     Generated charts and logs (created at runtime)
```

---

## How It Is Built for Scalability

### 1. Config is separated from logic
All breakpoints, AQI bins, units, and column aliases live in `config/pollutants.py`.
To add a new pollutant, add one entry to that file. Nothing else changes.

### 2. Agents share a common interface
Every agent inherits from `agents/base.py` which defines `perceive`, `act`, and `run`.
Switching agent types requires only `--agent model` on the command line.

| Agent          | File                      | Description                            |
|----------------|---------------------------|----------------------------------------|
| SimpleReflex   | agents/simple_reflex.py   | No memory. Rules on current percept.   |
| ModelBased     | agents/model_based.py     | Keeps a history window. Detects trend. |
| GoalBased      | (add when needed)         | Add agents/goal_based.py               |
| UtilityBased   | (add when needed)         | Add agents/utility_based.py            |
| Learning       | (add when needed)         | Add agents/learning_agent.py           |

### 3. Sensors share a common interface
Every sensor inherits from `sensors/base.py` which defines `read` and `read_all`.
To add a new data source, create a new file in `sensors/` and pass it to `Environment`.

| Sensor         | File                   | Description                        |
|----------------|------------------------|------------------------------------|
| CSVSensor      | sensors/csv_sensor.py  | Reads from Kaggle CSV files        |
| APISensor      | (add when needed)      | Add sensors/api_sensor.py          |
| StreamSensor   | (add when needed)      | Add sensors/stream_sensor.py       |

### 4. Plugins extend behavior without touching core logic
Plugins attach to the `Environment` and run after every agent decision.
To add new behavior, create a file in `plugins/`, inherit from `BasePlugin`, implement `process`.

| Plugin          | File                        | Description                          |
|-----------------|-----------------------------|--------------------------------------|
| Logger          | plugins/logger.py           | Appends every result to a CSV log    |
| ThresholdAlert  | plugins/threshold_alert.py  | Flags observations above a threshold |
| Notification    | (add when needed)           | Add plugins/notification.py          |
| Exporter        | (add when needed)           | Add plugins/json_exporter.py         |

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

Final AQI = sub-index of the dominant (worst) pollutant.
Source: India CPCB / SIM-air Working Paper Series #46-2021

---

## AQI Categories

| Range    | Category     |
|----------|--------------|
| 0 - 50   | Good         |
| 51 - 100 | Satisfactory |
| 101-200  | Moderate     |
| 201-300  | Poor         |
| 301-400  | Very Poor    |
| 401-500  | Severe       |

---

## Supported Pollutants

| Pollutant | Unit   | Averaging |
|-----------|--------|-----------|
| PM2.5     | ug/m3  | 24-hour   |
| PM10      | ug/m3  | 24-hour   |
| NO2       | ug/m3  | 24-hour   |
| SO2       | ug/m3  | 24-hour   |
| CO        | mg/m3  | 8-hour    |
| O3        | ug/m3  | 8-hour    |
| NH3       | ug/m3  | 24-hour   |
| Pb        | ug/m3  | 24-hour   |

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

# Specific row
python main.py --row 5

# Batch mode with model-based agent
python main.py --all --agent model

# Batch mode with charts, logging, and alerts
python main.py --all --visualize --log --alert 200

# Use your own dataset
python main.py --file path/to/data.csv --all --visualize
```

---

## Upgrading the Agent as the Course Progresses

Week 1 — Simple Reflex Agent (current):
    python main.py --agent simple

Week 2 — Model-Based Agent (built in, adds trend detection):
    python main.py --agent model

Week 3+ — Add a new agent type:
    1. Create agents/goal_based.py
    2. Inherit from BaseAgent
    3. Implement perceive() and act()
    4. Add "goal" to the --agent choices in main.py

No other files need to change.

---

## References

- Guttikunda, S. (2021). 10 Frequently Asked Questions on Air Quality Index.
  SIM-air Working Paper Series #46-2021.
- CPCB (2014). National Air Quality Index. Central Pollution Control Board, India.
- rohanrao (2020). Calculating AQI Tutorial. Kaggle.
- Russell, S. & Norvig, P. Artificial Intelligence: A Modern Approach. Chapter 2.
