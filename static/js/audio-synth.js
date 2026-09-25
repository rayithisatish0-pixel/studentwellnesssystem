/**
 * Serene Minds - Web Audio Synthesizer
 * Provides 100% self-contained ambient soundscapes and mindfulness chimes.
 * Requires no external audio assets; runs natively in any modern browser.
 */

class AudioSynthManager {
  constructor() {
    this.ctx = null;
    this.currentTrack = null;
    this.noiseNode = null;
    this.gainNode = null;
    this.isPlaying = false;
    this.currentSoundType = null;
  }

  initContext() {
    if (!this.ctx) {
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      this.ctx = new AudioContext();
    }
    if (this.ctx.state === 'suspended') {
      this.ctx.resume();
    }
  }

  playChime(freq = 528, duration = 2.5) {
    try {
      this.initContext();
      const osc = this.ctx.createOscillator();
      const gain = this.ctx.createGain();

      osc.type = 'sine';
      osc.frequency.setValueAtTime(freq, this.ctx.currentTime);

      gain.gain.setValueAtTime(0.001, this.ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.25, this.ctx.currentTime + 0.05);
      gain.gain.exponentialRampToValueAtTime(0.0001, this.ctx.currentTime + duration);

      osc.connect(gain);
      gain.connect(this.ctx.destination);

      osc.start(this.ctx.currentTime);
      osc.stop(this.ctx.currentTime + duration);
    } catch (e) {
      console.warn("Audio chime error:", e);
    }
  }

  playAmbient(type = 'rain') {
    this.initContext();
    this.stopAmbient();

    const bufferSize = this.ctx.sampleRate * 2;
    const noiseBuffer = this.ctx.createBuffer(1, bufferSize, this.ctx.sampleRate);
    const output = noiseBuffer.getChannelData(0);

    let b0 = 0, b1 = 0, b2 = 0, b3 = 0, b4 = 0, b5 = 0, b6 = 0;

    for (let i = 0; i < bufferSize; i++) {
      const white = Math.random() * 2 - 1;
      if (type === 'rain' || type === 'ocean') {
        // Pink / Brown noise filter
        b0 = 0.99886 * b0 + white * 0.0555179;
        b1 = 0.99332 * b1 + white * 0.0750759;
        b2 = 0.96900 * b2 + white * 0.1538520;
        b3 = 0.86650 * b3 + white * 0.3104856;
        b4 = 0.55000 * b4 + white * 0.5329522;
        b5 = -0.7616 * b5 - white * 0.0168980;
        output[i] = b0 + b1 + b2 + b3 + b4 + b5 + b6 + white * 0.5362;
        output[i] *= 0.11;
        b6 = white * 0.115926;
      } else {
        // Soft white noise
        output[i] = white * 0.06;
      }
    }

    const whiteNoise = this.ctx.createBufferSource();
    whiteNoise.buffer = noiseBuffer;
    whiteNoise.loop = true;

    // Filter setup
    const filter = this.ctx.createBiquadFilter();
    if (type === 'rain') {
      filter.type = 'lowpass';
      filter.frequency.value = 1000;
    } else if (type === 'ocean') {
      filter.type = 'bandpass';
      filter.frequency.value = 450;
      filter.Q.value = 1.0;

      // Add gentle undulating LFO to simulate ocean swells
      const lfo = this.ctx.createOscillator();
      const lfoGain = this.ctx.createGain();
      lfo.frequency.value = 0.12; // slow 8 second wave cycle
      lfoGain.gain.value = 250;
      lfo.connect(filter.frequency);
      lfo.start();
    } else {
      filter.type = 'lowpass';
      filter.frequency.value = 800;
    }

    this.gainNode = this.ctx.createGain();
    this.gainNode.gain.setValueAtTime(0.01, this.ctx.currentTime);
    this.gainNode.gain.linearRampToValueAtTime(0.3, this.ctx.currentTime + 1.5);

    whiteNoise.connect(filter);
    filter.connect(this.gainNode);
    this.gainNode.connect(this.ctx.destination);

    whiteNoise.start();
    this.noiseNode = whiteNoise;
    this.isPlaying = true;
    this.currentSoundType = type;
  }

  setVolume(volumePercent) {
    if (this.gainNode && this.ctx) {
      const vol = Math.max(0, Math.min(1, volumePercent / 100));
      this.gainNode.gain.linearRampToValueAtTime(vol * 0.5, this.ctx.currentTime + 0.1);
    }
  }

  stopAmbient() {
    if (this.noiseNode) {
      try {
        if (this.gainNode && this.ctx) {
          this.gainNode.gain.linearRampToValueAtTime(0.001, this.ctx.currentTime + 0.5);
        }
        setTimeout(() => {
          if (this.noiseNode) {
            this.noiseNode.stop();
            this.noiseNode.disconnect();
            this.noiseNode = null;
          }
        }, 500);
      } catch (e) {
        console.warn("Stop ambient error:", e);
      }
    }
    this.isPlaying = false;
    this.currentSoundType = null;
  }
}

const AudioSynth = new AudioSynthManager();
