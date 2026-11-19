package com.panocalm.xr

import android.media.AudioAttributes
import android.media.AudioFormat
import android.media.AudioTrack
import android.media.MediaCodec
import android.media.MediaExtractor
import android.media.MediaFormat
import java.io.File
import java.nio.ByteOrder

/**
 * Endless ambience without any "loop point" seen by the system: the sound file is decoded once to PCM, then written over and
 * over into one streaming AudioTrack that never ends and never seeks. (On the headset both ExoPlayer's and MediaPlayer's
 * looping went silent after the first pass while still reporting "playing".)
 */
class PcmLoop private constructor(private val pcm: ShortArray, private val rate: Int, private val channels: Int) {
    @Volatile private var running = true
    @Volatile private var paused = false
    private val lock = Object()
    /** how many full passes have been written, for the status line */
    @Volatile var passes = 0; private set
    private val track: AudioTrack
    private val thread: Thread

    init {
        val chMask = if (channels == 1) AudioFormat.CHANNEL_OUT_MONO else AudioFormat.CHANNEL_OUT_STEREO
        val minBuf = AudioTrack.getMinBufferSize(rate, chMask, AudioFormat.ENCODING_PCM_16BIT)
        track = AudioTrack.Builder()
            .setAudioAttributes(AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_MEDIA).setContentType(AudioAttributes.CONTENT_TYPE_MUSIC).build())
            .setAudioFormat(AudioFormat.Builder().setSampleRate(rate).setChannelMask(chMask).setEncoding(AudioFormat.ENCODING_PCM_16BIT).build())
            .setBufferSizeInBytes(maxOf(minBuf * 4, rate * channels * 2 / 2))     // ~0.5 s buffer
            .setTransferMode(AudioTrack.MODE_STREAM)
            .build()
        track.play()
        thread = Thread({
            val chunk = rate * channels / 10                                     // 100 ms per write
            var pos = 0
            while (running) {
                synchronized(lock) { while (paused && running) lock.wait() }
                if (!running) break
                val n = minOf(chunk, pcm.size - pos)
                val w = track.write(pcm, pos, n)                                  // blocking: paces the loop
                if (w < 0) { try { Thread.sleep(50) } catch (_: InterruptedException) { }; continue }
                pos += w
                if (pos >= pcm.size) { pos = 0; passes++ }
            }
        }, "calm360-ambience")
        thread.isDaemon = true
        thread.start()
    }

    val isPlaying: Boolean get() = running && !paused && track.playState == AudioTrack.PLAYSTATE_PLAYING

    fun pause() { paused = true; try { track.pause() } catch (_: Exception) { } }
    fun resume() { try { track.play() } catch (_: Exception) { }; synchronized(lock) { paused = false; lock.notifyAll() } }
    fun release() {
        running = false
        synchronized(lock) { lock.notifyAll() }
        try { track.pause(); track.flush(); track.release() } catch (_: Exception) { }
    }

    companion object {
        /** decode an .m4a/.mp3/.wav file to interleaved 16-bit PCM and start the endless loop */
        fun start(file: File): PcmLoop {
            val ex = MediaExtractor()
            ex.setDataSource(file.absolutePath)
            val ti = (0 until ex.trackCount).first { ex.getTrackFormat(it).getString(MediaFormat.KEY_MIME)?.startsWith("audio/") == true }
            ex.selectTrack(ti)
            val fmt = ex.getTrackFormat(ti)
            var rate = fmt.getInteger(MediaFormat.KEY_SAMPLE_RATE)
            var ch = fmt.getInteger(MediaFormat.KEY_CHANNEL_COUNT)
            val codec = MediaCodec.createDecoderByType(fmt.getString(MediaFormat.KEY_MIME)!!)
            codec.configure(fmt, null, null, 0); codec.start()
            val out = ArrayList<ShortArray>(); var total = 0
            val info = MediaCodec.BufferInfo(); var inDone = false; var outDone = false
            while (!outDone) {
                if (!inDone) {
                    val ib = codec.dequeueInputBuffer(10_000)
                    if (ib >= 0) {
                        val buf = codec.getInputBuffer(ib)!!
                        val sz = ex.readSampleData(buf, 0)
                        if (sz < 0) { codec.queueInputBuffer(ib, 0, 0, 0, MediaCodec.BUFFER_FLAG_END_OF_STREAM); inDone = true }
                        else { codec.queueInputBuffer(ib, 0, sz, ex.sampleTime, 0); ex.advance() }
                    }
                }
                val ob = codec.dequeueOutputBuffer(info, 10_000)
                when {
                    ob >= 0 -> {
                        if (info.size > 0) {
                            val bb = codec.getOutputBuffer(ob)!!.order(ByteOrder.nativeOrder())
                            bb.position(info.offset); bb.limit(info.offset + info.size)
                            val s = ShortArray(info.size / 2); bb.asShortBuffer().get(s); out += s; total += s.size
                        }
                        codec.releaseOutputBuffer(ob, false)
                        if (info.flags and MediaCodec.BUFFER_FLAG_END_OF_STREAM != 0) outDone = true
                    }
                    ob == MediaCodec.INFO_OUTPUT_FORMAT_CHANGED -> {
                        val of = codec.outputFormat
                        rate = of.getInteger(MediaFormat.KEY_SAMPLE_RATE); ch = of.getInteger(MediaFormat.KEY_CHANNEL_COUNT)
                    }
                }
            }
            codec.stop(); codec.release(); ex.release()
            val pcm = ShortArray(total); var p = 0
            for (s in out) { System.arraycopy(s, 0, pcm, p, s.size); p += s.size }
            require(pcm.isNotEmpty()) { "empty audio" }
            return PcmLoop(pcm, rate, ch)
        }
    }
}
