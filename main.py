from discord_webhook import DiscordWebhook, DiscordEmbed
from rtlsdr import RtlSdr
import numpy as np
import time

WIDEBAND_LENGTH = 2.56e6 # https://www.rtl-sdr.com/wp-content/uploads/2024/12/RTLSDR_V4_Datasheet_V_1_0.pdf Some newer models can technically do 3.2, but all of the values here are based on 2.56. You will have to compute all the other constants yourself if you choose to expand the scope of the wideband.
SCAN_ONE_CENTER     = 463.200e6
SCAN_TWO_CENTER = 466.800e6
# What you can really config
webhook = ""
embed_color="39FF14"
NFFT             = 256 * 1024
ALPHA            = 0.05
SIGNAL_THRESHOLD = 70 # really dependent on your setup. I got a lot of floor noise ~55 so I'm using 70. If you expect further away transmissions then maybe lower it
ALERT_COOLDOWN   = 5.0
CONFIRM_CYCLES   = 3 # Scanning both sweeps takes a decent amount of time, 3 should skip "transmissions" that are just rf spikes, adjust as needed
RETUNE_SLEEP     = 0.05
DC_NOTCH_MHZ = 0.05 # :frown: Should stop the rtl from having its crystal or whatever cause a spiking issue, reason why the scan centers are kinda abnormal xd

FRS_CHANNELS_MHZ = [462.5625, 462.5875, 462.6125, 462.6375, 462.6625, 462.6875, 462.7125,462.5500, 462.5750, 462.6000, 462.6250, 462.6500, 462.6750, 462.7000,467.5625, 467.5875, 467.6125, 467.6375, 467.6625, 467.6875, 467.7125,467.7000]
CHANNEL_BW_MHZ = 12500/1_000_000

sdr = RtlSdr()
sdr.sample_rate = WIDEBAND_LENGTH
sdr.gain = 'auto'

noise_one = None
noise_two = None
activity_tracker = {}
last_alert = {}
peak_db    = {}

def get_spectrum(center):
    try:
        time.sleep(RETUNE_SLEEP)
        sdr.center_freq = center
        samples  = sdr.read_samples(NFFT)
        window   = np.hanning(len(samples))
        fft_vals = np.fft.fftshift(np.fft.fft(samples * window))
        power    = 20 * np.log10(np.abs(fft_vals) + 1e-10)
        frequencies    = (np.fft.fftshift(
                        np.fft.fftfreq(len(samples), 1 / sdr.sample_rate)
                    ) + center) / 1e6
        dc_mask = np.abs(frequencies - center / 1e6) < DC_NOTCH_MHZ  # eradicate those evil spikes
        power[dc_mask] = -999

        return frequencies, power
    except Exception as e:
        print("Engine kaputt! " + str(e))
        return None, None

def channels_above_threshold(frequencies, normal_power):
    active = set()
    for i, channel in enumerate(FRS_CHANNELS_MHZ):
        mask = (frequencies >= channel - CHANNEL_BW_MHZ) & (frequencies <= channel + CHANNEL_BW_MHZ)
        if mask.any():
            channel_peak = normal_power[mask].max()
            if channel_peak >= SIGNAL_THRESHOLD:
                active.add(i)
                peak_db[i] = max(peak_db.get(i, 0), round(float(channel_peak), 1))
    return active


def handle_alerts(confirmed):
    now = time.time()
    for i in sorted(confirmed):
        if now - last_alert.get(i, 0) > ALERT_COOLDOWN:
            webhook_embed = DiscordWebhook(url=webhook)
            embed = DiscordEmbed(title="Activity Detected (FRS Band)", color=embed_color)

            # I am so tired of dynamic typing. Send me back home to java
            embed.add_embed_field(name="Time", value=time.strftime('%H:%M:%S'))
            embed.add_embed_field(name="Channel", value=str(i + 1))
            embed.add_embed_field(name="Frequency", value=str(FRS_CHANNELS_MHZ[i]))
            embed.add_embed_field(name="Signal", value=str(peak_db.get(i, '?')))

            webhook_embed.add_embed(embed)
            response = webhook_embed.execute()
            print("Webhook status code:", response.status_code)  # debug output
            last_alert[i] = now

try:
    while True:
        peak_db.clear()

        frequencies_one, power_a = get_spectrum(SCAN_ONE_CENTER)

        floor_one = np.percentile(power_a, 10)
        noise_one = floor_one if noise_one is None else ALPHA * floor_one + (1 - ALPHA) * noise_one
        normal_one  = np.clip(power_a - noise_one, 0, None)
        activity_one   = channels_above_threshold(frequencies_one, normal_one)

        frequencies_two, power_b = get_spectrum(SCAN_TWO_CENTER)

        floor_two = np.percentile(power_b, 10)
        noise_two = floor_two if noise_two is None else ALPHA * floor_two + (1 - ALPHA) * noise_two
        normal_two  = np.clip(power_b - noise_two, 0, None)
        activity_two   = channels_above_threshold(frequencies_two, normal_two)

        consolidated_activity = activity_one | activity_two

        confirmed = set()
        for i in consolidated_activity:
            activity_tracker[i] = activity_tracker.get(i, 0) + 1
            if activity_tracker[i] == CONFIRM_CYCLES:
                confirmed.add(i)

        if confirmed:
            handle_alerts(confirmed)

        for i in list(activity_tracker.keys()):
            if i not in consolidated_activity:
                activity_tracker[i] = 0

except KeyboardInterrupt:
    print("\nStopped.")
finally:
    sdr.close()
