# Constants
src_ports   = ["4433", "4434"]
pids        = [32, 33]
satellites  = [
    {
        'name'    : "Galaxy 18",
        'alias'   : "G18",
        'dl_freq' : 12016.92,
        'band'    : "Ku",
        'pol'     : "H"
    },
    {
        'name'    : "Eutelsat 113",
        'alias'   : "E113",
        'dl_freq' : 12026.15,
        'band'    : "Ku",
        'pol'     : "V"
    },
    {
        'name'    : "Telstar 11N Africa",
        'alias'   : "T11N AFR",
        'dl_freq' : 11476.75,
        'band'    : "Ku",
        'pol'     : "H"
    },
    {
        'name'    : "Telstar 11N Europe",
        'alias'   : "T11N EU",
        'dl_freq' : 11504.02,
        'band'    : "Ku",
        'pol'     : "V"
    },
    {
        'name'    : "Telstar 18V",
        'alias'   : "T18V",
        'dl_freq' : 4057.5,
        'band'    : "C",
        'pol'     : "H"
    },
    {
        'name'    : "Eutelsat 113 - Test carrier",
        'alias'   : "E113",
        'dl_freq' : 12066.9,
        'band'    : "Ku",
        'pol'     : "V"
    }
]

linux_usb_setup_type  = "Linux USB"
sdr_setup_type        = "Software-defined"
standalone_setup_type = "Standalone"

modems = [
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
        'vendor' : "TBS",
        'model'  : "5520SE",
        'type'   : linux_usb_setup_type
    },
    {
        'vendor' : "",
        'model'  : "RTL-SDR",
        'type'   : sdr_setup_type
    }
]

ku_band_thresh = 11700.0

lnbs = [
    {
        'vendor'    : "Avenger",
        'model'     : "PLL321S-2",
        'lo_freq'   : [9750.0, 10600],
        'universal' : True,
        'band'      : "Ku"

    },
    {
        'vendor'    : "Maverick",
        'model'     : "MK1",
        "lo_freq"   : 10750.0,
        'universal' : False,
        'band'      : "Ku"
    },
    {
        'vendor'    : "Titanium",
        'model'     : "C1",
        "lo_freq"   : 5150.0,
        'universal' : False,
        'band'      : "C"
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
