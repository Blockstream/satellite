# Constants
mcast_ip       = "239.0.0.2"
btc_port       = "4434"
btc_dst_addr   = mcast_ip + ":" + btc_port
src_ports      = ["4433", "4434"]
pids           = [32, 33]
rolloff        = 0.2
sym_rate = {
    'G18'      : 1000000,
    'E113'     : 1000000,
    'T11N AFR' : 1000000,
    'T11N EU'  : 1000000,
    'T18V C'   : 1000000,
    'T18V Ku'  : 1000000
}

low_rate_modcod  = "0x0010"
high_rate_modcod = "0x2000"

satellites  = [
    {
        'name'    : "Galaxy 18",
        'alias'   : "G18",
        'dl_freq' : 12016.4,
        'band'    : "Ku",
        'pol'     : "H",
        'ip'      : "172.16.235.1"
    },
    {
        'name'    : "Eutelsat 113",
        'alias'   : "E113",
        'dl_freq' : 12066.9,
        'band'    : "Ku",
        'pol'     : "V",
        'ip'      : "172.16.235.9"
    },
    {
        'name'    : "Telstar 11N Africa",
        'alias'   : "T11N AFR",
        'dl_freq' : 11480.7,
        'band'    : "Ku",
        'pol'     : "H",
        'ip'      : "172.16.235.17"
    },
    {
        'name'    : "Telstar 11N Europe",
        'alias'   : "T11N EU",
        'dl_freq' : 11484.3,
        'band'    : "Ku",
        'pol'     : "V",
        'ip'      : "172.16.235.25"
    },
    {
        'name'    : "Telstar 18V C Band",
        'alias'   : "T18V C",
        'dl_freq' : 4053.83,
        'band'    : "C",
        'pol'     : "H",
        'ip'      : "172.16.235.41"
    },
    {
        'name'    : "Telstar 18V Ku Band",
        'alias'   : "T18V Ku",
        'dl_freq' : 11506.75,
        'band'    : "Ku",
        'pol'     : "H",
        'ip'      : "172.16.235.49"
    }
]

linux_usb_setup_type  = "Linux USB"
sdr_setup_type        = "Software-defined"
standalone_setup_type = "Standalone"

demods = [
    {
        'vendor' : "Novra",
        'model'  : "S400",
        'type'   : standalone_setup_type
    },
    {
        'vendor' : "TBS",
        'model'  : "5927",
        'type'   : linux_usb_setup_type
    },
    {
        'vendor' : "",
        'model'  : "RTL-SDR",
        'type'   : sdr_setup_type
    }
]

antennas = [
    { 'label' : "45cm / 18in",  'type': 'dish', 'size' : 45   },
    { 'label' : "60cm / 24in",  'type': 'dish', 'size' : 60   },
    { 'label' : "76cm / 30in",  'type': 'dish', 'size' : 76   },
    { 'label' : "90cm / 36in",  'type': 'dish', 'size' : 90   },
    { 'label' : "1.2m / 4ft",   'type': 'dish', 'size' : 120  },
    { 'label' : "1.5m / 5ft",   'type': 'dish', 'size' : 150  },
    { 'label' : "1.8m / 6ft",   'type': 'dish', 'size' : 180  },
    { 'label' : "2.4m / 8ft",   'type': 'dish', 'size' : 240  },
    { 'label' : 'Blockstream',  'type': 'flat', 'size' : None },
]

ku_band_thresh = 11700.0

lnbs = [
    {
        'vendor'    : "Avenger",
        'model'     : "PLL321S-2",
        'lo_freq'   : [9750.0, 10600.0],
        'universal' : True,
        'band'      : "Ku",
        'pol'       : "Dual"
    },
    {
        'vendor'    : "Maverick",
        'model'     : "MK1",
        "lo_freq"   : 10750.0,
        'universal' : False,
        'band'      : "Ku",
        'pol'       : "Dual"
    },
    {
        'vendor'    : "GEOSATpro",
        'model'     : "UL1PLL",
        'lo_freq'   : [9750.0, 10600.0],
        'universal' : True,
        'band'      : "Ku",
        'pol'       : "Dual"
    },
    {
        'vendor'    : "Titanium",
        'model'     : "C1",
        "lo_freq"   : 5150.0,
        'universal' : False,
        'band'      : "C",
        'pol'       : "Dual"
    },
    {
        'vendor'    : "Selfsat",
        'model'     : "H50D",
        'lo_freq'   : [9750.0, 10600.0],
        'universal' : True,
        'band'      : "Ku",
        'pol'       : "Dual"
    }
]

psus = [
    {
        "model"   : "Directv 21 Volt Power Inserter for SWM",
        "voltage" : 21
    },
    {
        "model"   : "AT&T 21 Volt Power Inserter for SWM",
        "voltage" : 21
    }
]

v4l_lnbs = [
    {
        'alias' : "UNIVERSAL",
        'lowfreq' : 9750,
        'highfreq' : 10600,
        'rangeswitch' : 11700,
        'freqrange' : [
            ( 10800, 11800 ),
            ( 11600, 12700 ),
        ]
    }, {
        'alias' : "DBS",
        'lowfreq' : 11250,
        'freqrange' : [
            ( 12200, 12700 )
        ]
    }, {
        'alias' : "EXTENDED",
        'lowfreq' : 9750,
        'highfreq' : 10600,
        'rangeswitch' : 11700,
        'freqrange' : [
            ( 10700, 11700 ),
            ( 11700, 12750 ),
        ]
    }, {
        'alias' : "STANDARD",
        'lowfreq' : 10000,
        'freqrange' : [
            ( 10945, 11450 )
        ]
    }, {
        'alias' : "L10700",
        'lowfreq' : 10700,
        'freqrange' : [
            ( 11750, 12750 )
        ]
    }, {
        'alias' : "L10750",
        'lowfreq' : 10750,
        'freqrange' : [
            ( 11700, 12200 )
        ]
    }, {
        'alias' : "L11300",
        'lowfreq' : 11300,
        'freqrange' : [
            ( 12250, 12750 )
        ]
    }, {
        'alias' : "ENHANCED",
        'lowfreq' : 9750,
        'freqrange' : [
            ( 10700, 11700 )
        ]
    }, {
        'alias' : "QPH031",
        'lowfreq' : 10750,
        'highfreq' : 11250,
        'rangeswitch' : 12200,
        'freqrange' : [
            ( 11700, 12200 ),
            ( 12200, 12700 ),
        ]
    }, {
        'alias' : "C-BAND",
        'lowfreq' : 5150,
        'freqrange' : [
            ( 3700, 4200 )
        ]
    }, {
        'alias' : "C-MULT",
        'lowfreq' : 5150,
        'highfreq' : 5750,
        'freqrange' : [
            ( 3700, 4200 )
        ]
    }, {
        'alias' : "DISHPRO",
        'lowfreq' : 11250,
        'highfreq' : 14350,
        'freqrange' : [
            ( 12200, 12700 )
        ]
    }, {
        'alias' : "110BS",
        'lowfreq' : 10678,
        'freqrange' : [
            ( 11710, 12751 )
        ]
    }, {
        'alias' : "STACKED-BRASILSAT",
        'lowfreq' : 9710,
        'highfreq' : 9750,
        'freqrange' : [
            ( 10700, 11700 ),
        ]
    }, {
        'alias' : "OI-BRASILSAT",
        'lowfreq' : 10000,
        'highfreq' : 10445,
        'rangeswitch' : 11700,
        'freqrange' : [
            ( 10950, 11200 ),
            ( 11800, 12200 ),
        ]
    }
]

lnb_options = [x['alias'] for x in v4l_lnbs]
