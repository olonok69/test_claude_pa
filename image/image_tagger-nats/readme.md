# Image Processing Service

This service handles image processing tasks via NATS messaging, supporting two operational modes: **tagging** and **captioning**. Each mode operates independently to optimize resource usage and simplify management.

## Overview

The Image Processing Service is built around a NATS JetStream messaging system that allows asynchronous processing of images. The application can operate in one of two modes:

1. **Tagging Mode**: Identifies objects and elements in images and generates tags
2. **Captioning Mode**: Generates detailed textual descriptions of image content

Each mode is configured to run separately, as determined by the `DOCKER_TASK` environment variable.

## Architecture

### Components

- **NATS Server**: Message broker for task distribution and result collection
- **Producer**: Publishes image processing tasks to NATS streams
- **Consumer (this service)**: Processes images using Florence-2 AI model
- **Florence-2 Model**: Deep learning model for image analysis

### Flow

1. Producer publishes image tasks to the appropriate NATS subject:
   - `tagger.tasks.started.>` for tagging tasks
   - `caption.tasks.started.>` for captioning tasks

2. The service subscribes to the appropriate subject based on its mode

3. The service processes images and publishes results to:
   - `tagger.results.completed.>` for tagging results
   - `caption.results.completed.>` for captioning results

## Configuration

### Environment Variables

The service is configured using environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `DOCKER_TASK` | Operation mode (either "tagger" or "caption") | "tagger" |
| `MODEL_PATH` | Path to the AI model | Varies by platform |
| `LOCAL_ENV` | Flag for local development mode | "0" |
| `USE_ONNX` | Flag to use ONNX runtime | "NO" |
| `USE_OPENVINO` | Flag to use OpenVINO | "YES" |
| `DEVICE_OV` | Device for OpenVINO (CPU/GPU) | "CPU" |
| `INPUT_STREAM` | NATS input stream name | "IMAGE-TASKS" |
| `OUTPUT_STREAM` | NATS output stream name | "IMAGE-RESULTS" |
| `NAT_URL` | NATS server URL | "nats://localhost:4222" |

### Subjects

The service uses the following NATS subjects:

- **Input subjects**:
  - Tagging: `tagger.tasks.started.>` 
  - Captioning: `caption.tasks.started.>`

- **Output subjects**:
  - Tagging: `tagger.results.completed.>`
  - Captioning: `caption.results.completed.>`

## Usage

### Running the Service

1. Set the `.env_file` with appropriate configuration values

2. Run the service in the desired mode:

   ```bash
   # For tagging mode
   DOCKER_TASK=tagger python main.py

   # For captioning mode
   DOCKER_TASK=caption python main.py
   ```

3. The service will:
   - Load the Florence-2 model
   - Set up NATS streams and subscriptions for the selected mode
   - Process incoming image tasks in the background

### Using the Producer

The service includes a producer notebook (`producer_tagger-files.py`) that can be used to send image processing tasks:

```python
# For tagging mode
await process_folder_with_mode(INPUT_DIR, mode="tagging", num_labels=5, prompt="OD")

# For captioning mode
await process_folder_with_mode(INPUT_DIR, mode="captioning", prompt="MORE_DETAILED_CAPTION")
```

### Message Format

The input message format for image tasks:

```json
{
  "source": {
    "uri": "file:///path/to/image.jpg",
    "type": "image"
  },
  "state": {
    "status": "STARTED",
    "timestamp": "2025-05-12T10:33:05.123456"
  },
  "prompt": "OD",
  "num_labels": 5  // Only for tagging mode
}
```

## Operational Modes

### Tagging Mode

When running in tagging mode (`DOCKER_TASK=tagger`):

- The service subscribes to `tagger.tasks.started.>`
- It processes images to identify objects and generate tags
- Results are published to `tagger.results.completed.>`
- The `OD` prompt is used with the Florence-2 model
- The `num_labels` parameter controls how many tags are generated

### Captioning Mode

When running in captioning mode (`DOCKER_TASK=caption`):

- The service subscribes to `caption.tasks.started.>`
- It generates detailed textual descriptions of images
- Results are published to `caption.results.completed.>`
- The `MORE_DETAILED_CAPTION` prompt is used with the Florence-2 model

## Key Features

1. **Mode-specific Operation**: Runs in a single mode to optimize resources
2. **Detailed Logging**: Comprehensive logging for operational monitoring
3. **Pull-based Subscription**: Uses durable pull subscribers to ensure message delivery
4. **Error Handling**: Robust error handling for each processing step
5. **Configurable Model**: Supports multiple AI model backends (ONNX, OpenVINO)

## Troubleshooting

### Common Issues

1. **Messages not being processed**:
   - Ensure NATS server is running
   - Verify subject names match between producer and consumer
   - Check if durable consumer is configured correctly

2. **Model loading errors**:
   - Verify the model path is correct
   - Ensure the Florence-2 model files are present

3. **NATS connection issues**:
   - Check if NATS server is accessible
   - Verify credentials if authentication is enabled

### Diagnostic Tools

The repository includes diagnostic tools:

1. **NATS Diagnostic Tool**: Inspects NATS streams and messages
2. **Test Message Sender**: Sends test messages to verify service operation

## Development

### Directory Structure

```
├── main.py                  # Main application entry point
├── Dockerfile-captioner     # DockerFile captioner
├── Dockerfile-tagger        # DockerFile tagger
├── requirements.txt         # python libraries
├── utils/
│   ├── message_handlers.py  # NATS message processing
│   ├── nats_utils.py        # NATS stream setup
│   ├── schemas.py           # Message schemas
│   ├── environment.py       # check which type of environment the app is runing
│   ├── ssl_utils.py         # class to manage the nats TLS connection
│   └── utils.py             # Setup paths and Environments
├── src/
│   ├── ov_florence2_helper.py  # Class to load Florence2 in OpenVino IR format
│   ├── predictor.py         # Load Model and Inference
│   ├── utils_captioning.py  # AI model interface captioning Mode
│   ├── utils_tagging.py     # AI model interface tagging Mode
│   ├── schemas.py           # old schemas taggings before merge with captioning
│   └── utils.py             # old tagging utils , before merge with captioning
├── keys/
│   └── .env_file            # Environment config
├── models/                  # AI model files
│   └── Florence-2-base-ft/
├── images/                  # Test images
└── logs/                    # Application logs
```

### Extending the Service

To add new functionality:

1. **New processing mode**:
   - Add a new conditional branch in `main.py`
   - Create new subject handlers in `message_handlers.py`

2. **New model support**:
   - Add model loading code in `predictor.py`
   - Update environment variables for model configuration

## License

[Specify your license information here]

## Contributors

[List contributors here]