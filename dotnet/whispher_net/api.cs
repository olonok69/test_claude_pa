
//Install-Package SkiaSharp
// Install-Package FFMpegCore -version 5.1.0
// Install-Package FFMpegCore.Extensions.SkiaSharp
// Install-Package FFMpegCore.Extensions.System.Drawing.Common


using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using System;
using System.Diagnostics;
using System.IO;
using System.Threading.Tasks;
using System.Threading;
using System.Drawing;
using FFMpegCore;
using FFMpegCore.Enums;
using FFMpegCore.Extensions.SkiaSharp;
using FFMpegCore.Extensions.System.Drawing.Common;
using FFMpegCore.Pipes;
using SkiaSharp;
using FFMpegImage = FFMpegCore.Extensions.System.Drawing.Common.FFMpegImage;
using Whisper.net;
using Whisper.net.Ggml;



namespace AudioUpload.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class AudioController : ControllerBase
    {
        private readonly string _modelPath;
        private readonly IWebHostEnvironment _env;
        private readonly string _ffmpegPath = "/usr/bin/ffmpeg"; // Linux FFmpeg path

        // Constructor to inject the model path (best practice)
        public AudioController(IWebHostEnvironment env) // Inject IWebHostEnvironment
        {
            _env = env;
            // Example: Model in wwwroot folder. Adjust path as needed.
            _modelPath = Path.Combine(env.ContentRootPath, "ggml-base.bin");

            // Check if the model file exists (important!)
            if (!System.IO.File.Exists(_modelPath))
            {
                DownloadModelIfNeeded().Wait(); // Download if needed.
            }
        }

        private async Task DownloadModelIfNeeded()
        {
            if (!System.IO.File.Exists(_modelPath))
            {
                var ggmlType = GgmlType.Base;
                var modelFileName = "ggml-base.bin";
                await DownloadModel(modelFileName, ggmlType);
            }
        }

        private async Task DownloadModel(string modelFileName, GgmlType ggmlType)
        {
            try
            {
                var modelUri = ggmlType switch
                {
                    GgmlType.Tiny => "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-tiny.bin",
                    GgmlType.Base => "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.bin",
                    GgmlType.Small => "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.bin",
                    GgmlType.Medium => "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-medium.bin",
                    GgmlType.LargeV1 => "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-large.bin",
                    _ => throw new ArgumentOutOfRangeException(nameof(ggmlType), ggmlType, null)
                };

                using var httpClient = new HttpClient();
                var response = await httpClient.GetAsync(modelUri, HttpCompletionOption.ResponseHeadersRead);
                response.EnsureSuccessStatusCode();

                using var contentStream = await response.Content.ReadAsStreamAsync();
                using var fileStream = new FileStream(_modelPath, FileMode.Create, FileAccess.Write, FileShare.None, 8192, true);
                await contentStream.CopyToAsync(fileStream);

                Console.WriteLine($"Downloaded model to {_modelPath}");
            }
            catch (Exception ex)
            {
                Console.WriteLine($"Error downloading model: {ex.Message}");
                throw; // Re-throw to indicate download failure.
            }
        }



        [HttpPost("upload")]
        public async Task<IActionResult> UploadAudio(IFormFile audioFile, bool translate = false)
        {
            if (audioFile == null || audioFile.Length == 0)
            {
                return BadRequest("No audio file received.");
            }

            if (audioFile.ContentType != "audio/mpeg" &&
                audioFile.ContentType != "audio/wav" &&
                audioFile.ContentType != "audio/x-wav")
            {
                return BadRequest("Invalid audio file format. Only MP3, WAV and x-WAV files are allowed.");
            }

            try
            {
                Stopwatch stopwatch = Stopwatch.StartNew();
                string tempInputPath = Path.Combine(Path.GetTempPath(), Path.GetRandomFileName() + Path.GetExtension(audioFile.FileName));
                string tempOutputPath = Path.Combine(Path.GetTempPath(), Path.GetRandomFileName() + ".wav");

                // Save uploaded file
                using (var stream = new FileStream(tempInputPath, FileMode.Create))
                {
                    await audioFile.CopyToAsync(stream);
                }

                try
                {
                    // Configure FFmpeg binary folder
                    GlobalFFOptions.Configure(options => options.BinaryFolder = "/usr/bin");

                    // Convert to 16kHz WAV using FFmpeg
                    FFMpegArguments
                        .FromFileInput(tempInputPath)
                        .OutputToFile(tempOutputPath, true, options => options
                            .WithCustomArgument("-acodec pcm_s16le")
                            .WithCustomArgument("-ac 1")
                            .WithCustomArgument("-ar 16000"))
                        .ProcessSynchronously();

                    // Process the converted file
                    using (var audioStream = System.IO.File.OpenRead(tempOutputPath))
                    {
                        string transcribedText = await TranscribeAudioWithWhisper(audioStream, translate);

                        stopwatch.Stop();
                        long executionTimeMs = stopwatch.ElapsedMilliseconds;

                        return Ok(new
                        {
                            Message = "Audio transcribed.",
                            Transcription = transcribedText,
                            ExecutionTimeMs = executionTimeMs
                        });
                    }
                }
                finally
                {
                    // Cleanup temporary files
                    if (System.IO.File.Exists(tempInputPath)) System.IO.File.Delete(tempInputPath);
                    if (System.IO.File.Exists(tempOutputPath)) System.IO.File.Delete(tempOutputPath);
                }
            }
            catch (Exception ex)
            {
                return StatusCode(500, $"Internal server error: {ex.Message}");
            }
        }

        private async Task<string> TranscribeAudioWithWhisper(Stream audioStream, bool translate)
        {
            var whisperFactory = WhisperFactory.FromPath(_modelPath); // Use the stored path
            var builder = whisperFactory.CreateBuilder()
                .WithLanguage("auto");

            if (translate)
            {
                builder = builder.WithTranslate();
            }

            using var processor = builder.Build();

            var transcription = "";
            await foreach (var result in processor.ProcessAsync(audioStream))
            {
                transcription += $"{result.Start}->{result.End}: {result.Text}\n";
            }

            return transcription;
        }
    }
}