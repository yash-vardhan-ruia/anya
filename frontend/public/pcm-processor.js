class PCMProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    // Use a smaller buffer size to minimize latency
    this.bufferSize = 1024;
    this.buffer = new Float32Array(this.bufferSize);
    this.bufferIndex = 0;
  }

  process(inputs, outputs, parameters) {
    const input = inputs[0];
    if (!input || !input[0]) return true;

    const channelData = input[0]; // Mono channel

    for (let i = 0; i < channelData.length; i++) {
      this.buffer[this.bufferIndex++] = channelData[i];

      if (this.bufferIndex >= this.bufferSize) {
        // Downsample the buffer from the browser's context sampleRate to 16000Hz
        const downsampled = this.downsample(this.buffer, sampleRate, 16000);
        // Convert Float32 downsampled array to Int16 PCM
        const int16Buffer = this.float32ToInt16(downsampled);
        // Post raw PCM buffer to main thread
        this.port.postMessage(int16Buffer.buffer, [int16Buffer.buffer]);

        this.bufferIndex = 0;
      }
    }

    return true;
  }

  downsample(buffer, fromRate, toRate) {
    if (fromRate === toRate) {
      return buffer;
    }
    const sampleRateRatio = fromRate / toRate;
    const newLength = Math.round(buffer.length / sampleRateRatio);
    const result = new Float32Array(newLength);
    let offsetResult = 0;
    let offsetBuffer = 0;

    while (offsetResult < result.length) {
      const nextOffsetBuffer = Math.round((offsetResult + 1) * sampleRateRatio);
      let accum = 0;
      let count = 0;
      for (let i = offsetBuffer; i < nextOffsetBuffer && i < buffer.length; i++) {
        accum += buffer[i];
        count++;
      }
      result[offsetResult] = count > 0 ? accum / count : 0;
      offsetResult++;
      offsetBuffer = nextOffsetBuffer;
    }
    return result;
  }

  float32ToInt16(buffer) {
    const result = new Int16Array(buffer.length);
    for (let i = 0; i < buffer.length; i++) {
      const s = Math.max(-1, Math.min(1, buffer[i]));
      result[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
    }
    return result;
  }
}

registerProcessor('pcm-processor', PCMProcessor);
