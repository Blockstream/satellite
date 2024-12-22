import copy

# Constants
user_guide_url = "https://blockstream.github.io/satellite/"
blocksat_pubkey = '87D07253F69E4CD8629B0A21A94A007EC9D4458C'
mcast_ip = "239.0.0.2"
api_port = 4433
btc_port = 4434
monitor_port = 4435
api_dst_addr = mcast_ip + ":" + str(api_port)
btc_dst_addr = mcast_ip + ":" + str(btc_port)
src_ports = [str(api_port), str(btc_port)]
pids = [32]
rolloff = 0.2
fecframe_size = 'normal'
pilots = True
sym_rate = {
    'G18': 1000000,
    'T11N AFR': 1000000,
    'T11N EU': 1000000,
    'T18V C': 1000000,
    'T18V Ku': 1000000
}
default_standalone_ip_addr = "192.168.1.2"
api_server_url = {
    'main': "https://api.blockstream.space",
    'test': "https://api.blockstream.space/testnet"
}

satellites = [{
    'name': "Galaxy 18",
    'alias': "G18",
    'dl_freq': 11913.4,
    'band': "Ku",
    'pol': "H",
    'ip': "172.16.235.1",
    'region': 0
}, {
    'name': "Telstar 11N Africa",
    'alias': "T11N AFR",
    'dl_freq': 11452.1,
    'band': "Ku",
    'pol': "H",
    'ip': "172.16.235.17",
    'region': 2
}, {
    'name': "Telstar 11N Europe",
    'alias': "T11N EU",
    'dl_freq': 11505.4,
    'band': "Ku",
    'pol': "V",
    'ip': "172.16.235.25",
    'region': 3
}, {
    'name': "Telstar 18V C Band",
    'alias': "T18V C",
    'dl_freq': 4122.6,
    'band': "C",
    'pol': "V",
    'ip': "172.16.235.41",
    'region': 4
}, {
    'name': "Telstar 18V Ku Band",
    'alias': "T18V Ku",
    'dl_freq': 11507.9,
    'band': "Ku",
    'pol': "H",
    'ip': "172.16.235.49",
    'region': 5
}]
satellites_as_dict = {sat['alias']: sat for sat in satellites}
satellite_regions = [sat['region'] for sat in satellites]
decommissioned_satellites = ["E113"]

linux_usb_setup_type = "Linux USB"
sdr_setup_type = "Software-defined"
standalone_setup_type = "Standalone"
sat_ip_setup_type = "Sat-IP"

demods = [
    {
        'vendor': "Novra",
        'model': "S400",
        'type': standalone_setup_type,
        'tun_range': [950.0, 2150.0]
    },
    {
        'vendor': "TBS",
        'model': "5927",
        'type': linux_usb_setup_type,
        'tun_range': [950.0, 2150.0]
    },
    {
        'vendor': "TBS",
        'model': "5520SE",
        'type': linux_usb_setup_type,
        'tun_range': [950.0, 2150.0]
    },
    {
        'vendor': "",
        'model': "RTL-SDR",
        'type': sdr_setup_type,
        'tun_range': [24.0, 1766.0]  # assuming R820T2
    },
    {
        'vendor': "Selfsat",
        'model': "IP22",
        'type': sat_ip_setup_type,
        'tun_range': [950, 2150]
    }
]

antennas = [{
    'label': "45cm / 18in",
    'type': 'dish',
    'size': 45
}, {
    'label': "60cm / 24in",
    'type': 'dish',
    'size': 60
}, {
    'label': "76cm / 30in",
    'type': 'dish',
    'size': 76
}, {
    'label': "90cm / 36in",
    'type': 'dish',
    'size': 90
}, {
    'label': "1.2m / 4ft",
    'type': 'dish',
    'size': 120
}, {
    'label': "1.5m / 5ft",
    'type': 'dish',
    'size': 150
}, {
    'label': "1.8m / 6ft",
    'type': 'dish',
    'size': 180
}, {
    'label': "2.4m / 8ft",
    'type': 'dish',
    'size': 240
}, {
    'label': 'Selfsat-H50D',
    'type': 'flat',
    'size': None
}, {
    'label': 'Selfsat>IP22',
    'type': 'sat-ip',
    'size': None
}]

ku_band_thresh = 11700.0

lnbs = [{
    'vendor': "GEOSATpro",
    'model': "UL1PLL",
    'in_range': [10700.0, 12750.0],
    'lo_freq': [9750.0, 10600.0],
    'universal': True,
    'band': "Ku",
    'pol': "Dual"
}, {
    'vendor': "Titanium",
    'model': "C1-PLL",
    'in_range': [3700.0, 4200.0],
    "lo_freq": 5150.0,
    'universal': False,
    'band': "C",
    'pol': "Dual"
}, {
    'vendor': "Selfsat",
    'model': "Integrated LNB",
    'in_range': [10700.0, 12750.0],
    'lo_freq': [9750.0, 10600.0],
    'universal': True,
    'band': "Ku",
    'pol': "Dual"
}, {
    'vendor': "Avenger",
    'model': "PLL321S-2",
    'in_range': [10700.0, 12750.0],
    'lo_freq': [9750.0, 10600.0],
    'universal': True,
    'band': "Ku",
    'pol': "Dual"
}, {
    'vendor': "Maverick",
    'model': "MK1-PLL",
    'in_range': [11700.0, 12200.0],
    "lo_freq": 10750.0,
    'universal': False,
    'band': "Ku",
    'pol': "Dual"
}, {
    'vendor': " Mediastar",
    'model': "A381",
    'in_range': [3800.0, 4100.0],
    "lo_freq": 5150.0,
    'universal': False,
    'band': "C",
    'pol': "Dual"
}]

psus = [{
    "model": "Directv 21 Volt Power Inserter for SWM",
    "voltage": 21
}, {
    "model": "AT&T 21 Volt Power Inserter for SWM",
    "voltage": 21
}]

v4l_lnbs = [{
    'alias': "UNIVERSAL",
    'lowfreq': 9750,
    'highfreq': 10600,
    'rangeswitch': 11700,
    'freqrange': [
        (10800, 11800),
        (11600, 12700),
    ]
}, {
    'alias': "DBS",
    'lowfreq': 11250,
    'freqrange': [(12200, 12700)]
}, {
    'alias': "EXTENDED",
    'lowfreq': 9750,
    'highfreq': 10600,
    'rangeswitch': 11700,
    'freqrange': [
        (10700, 11700),
        (11700, 12750),
    ]
}, {
    'alias': "STANDARD",
    'lowfreq': 10000,
    'freqrange': [(10945, 11450)]
}, {
    'alias': "L10700",
    'lowfreq': 10700,
    'freqrange': [(11750, 12750)]
}, {
    'alias': "L10750",
    'lowfreq': 10750,
    'freqrange': [(11700, 12200)]
}, {
    'alias': "L11300",
    'lowfreq': 11300,
    'freqrange': [(12250, 12750)]
}, {
    'alias': "ENHANCED",
    'lowfreq': 9750,
    'freqrange': [(10700, 11700)]
}, {
    'alias': "QPH031",
    'lowfreq': 10750,
    'highfreq': 11250,
    'rangeswitch': 12200,
    'freqrange': [
        (11700, 12200),
        (12200, 12700),
    ]
}, {
    'alias': "C-BAND",
    'lowfreq': 5150,
    'freqrange': [(3700, 4200)]
}, {
    'alias': "C-MULT",
    'lowfreq': 5150,
    'highfreq': 5750,
    'freqrange': [(3700, 4200)]
}, {
    'alias': "DISHPRO",
    'lowfreq': 11250,
    'highfreq': 14350,
    'freqrange': [(12200, 12700)]
}, {
    'alias': "110BS",
    'lowfreq': 10678,
    'freqrange': [(11710, 12751)]
}, {
    'alias': "STACKED-BRASILSAT",
    'lowfreq': 9710,
    'highfreq': 9750,
    'freqrange': [
        (10700, 11700),
    ]
}, {
    'alias': "OI-BRASILSAT",
    'lowfreq': 10000,
    'highfreq': 10445,
    'rangeswitch': 11700,
    'freqrange': [
        (10950, 11200),
        (11800, 12200),
    ]
}]

modcods = {
    'qpsk1/4': 1,
    'qpsk1/3': 2,
    'qpsk2/5': 3,
    'qpsk1/2': 4,
    'qpsk3/5': 5,
    'qpsk2/3': 6,
    'qpsk3/4': 7,
    'qpsk4/5': 8,
    'qpsk5/6': 9,
    'qpsk8/9': 10,
    'qpsk9/10': 11,
    '8psk3/5': 12,
    '8psk2/3': 13,
    '8psk3/4': 14,
    '8psk5/6': 15,
    '8psk8/9': 16,
    '8psk9/10': 17,
    '16apsk2/3': 18,
    '16apsk3/4': 19,
    '16apsk4/5': 20,
    '16apsk5/6': 21,
    '16apsk8/9': 22,
    '16apsk9/10': 23,
    '32apsk3/4': 24,
    '32apsk4/5': 25,
    '32apsk5/6': 26,
    '32apsk8/9': 27,
    '32apsk9/10': 28
}

lnb_options = [x['alias'] for x in v4l_lnbs]

supported_metrics_per_receiver = {
    "standalone": ["level", "lock", "snr", "ber", "pkt_err"],
    "sdr": {
        'leandvb': ["level", "lock", "snr", "ber"],
        'gr-dvbs2rx': ["lock", "snr", "fer", "per", "pkt_err"]
    },
    "usb": ["level", "lock", "snr", "ber"],
    "sat-ip": ["level", "lock", "quality"]
}


def get_satellite_def(alias):
    for satellite in satellites:
        if satellite['alias'] == alias:
            return copy.deepcopy(satellite)
    raise ValueError(f"Invalid satellite alias {alias}")


def get_demod_def(vendor, model):
    for demod in demods:
        if demod['vendor'] == vendor and demod['model'] == model:
            return copy.deepcopy(demod)
    raise ValueError(f"Invalid demodulator {vendor} {model}")


def get_antenna_def(label):
    for antenna in antennas:
        if label in antenna['label']:
            return copy.deepcopy(antenna)
    raise ValueError(f"Invalid antenna {label}")


def get_lnb_def(vendor, model):
    for lnb in lnbs:
        if lnb['vendor'] == vendor and lnb['model'] == model:
            return copy.deepcopy(lnb)
    raise ValueError(f"Invalid LNB {vendor} {model}")
