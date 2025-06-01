# Summarize and Transcribe Videos with Gemini Pro


# Requirements
ffmpeg, Ubuntu, python3.11, requirements.txt, and account in Google Cloud and service principal account credential and Gemini API key

## FFMPEG
FFmpeg is the leading multimedia framework, able to decode, encode, transcode, mux, demux, stream, filter and play pretty much anything that humans and machines have created. It supports the most obscure ancient formats up to the cutting edge. No matter if they were designed by some standards committee, the community or a corporation. It is also highly portable: FFmpeg compiles, runs, and passes our testing infrastructure FATE across Linux, Mac OS X, Microsoft Windows, the BSDs, Solaris, etc. under a wide variety of build environments, machine architectures, and configurations.

## MoviePy
MoviePy is the Python reference tool for video editing automation.

It’s an open source, MIT-licensed library offering user-friendly video editing and manipulation tools for the Python programming language.


## Links
- https://zulko.github.io/moviepy/user_guide/loading.html
- https://ffmpeg.org/


```mermaid
graph TD
    A[Start] --> B{Load Environment Variables and Configuration};
    B --> C{Initialize Vertex AI};
    C --> D{Check API Keys in Environment};
    D -- Not Present --> E[Set API Keys from Config];
    E --> F[Initialize Language Model];
    D -- Present --> F[Initialize Language Model];
    F --> G{Convert Video to Audio};
    G --> H{Upload Audio to Cloud Storage};
    H --> I{Generate Text Summary};
    I --> J{Print Text Summary};
    J --> K{Generate Full Transcription};
    K --> L{Print Full Transcription};
    L --> M[End];
