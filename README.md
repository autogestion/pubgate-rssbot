## PubGate RSS Bot
Extension for [PubGate](https://github.com/autogestion/pubgate), federates rss-feeds

Requires PubGate >= 0.2.2
### Run

 - Install PubGate
 - Install rssbot
 ```
 pip install git+https://github.com/autogestion/pubgate-rssbot.git

```
 - Update conf.cfg with
```
EXTENSIONS = [..., "rssbot"]
RSSBOT_TIMEOUT = 3600
```
 - run 
```
python run_api.py

```


### Usage

#### Create bot
```
/user  POST
```
payload
```
{
	"username": "user",
	"password": "pass",
	"email": "admin@mail.com",                                     #optional
	"invite": "xyz",                                               #required if register by invite enabled
	"profile": {
		"type": "Service",
		"preferredUsername": "Anarchy101",
		"summary": "For questions about the theory of anarchism, anarchist movements, opinions on certain situations or current events, or even socialist or communist theory in general.",
	    "icon": {
	        "type": "Image",
	        "mediaType": "image/png",
	        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7a/Anarchy-symbol.svg/1200px-Anarchy-symbol.svg.png"
	    }		
	}
	"details": {
		"rssbot": {
			"feed": "https://www.reddit.com/r/Anarchy101/.rss",
			"enable": true,
			"tags": ["anarchy", "anarchy101", "reddit"]       #could be empty []
			"html": true                                      #if false, title will be used
		}
	}
}
```

#### Disable/Update bot
```
/<username>  PATCH   (auth required)
```
payload
```
{
    "details": {
        "rssbot": {
            "feed": "https://www.reddit.com/r/Anarchy101/.rss",           #change to update feed url
            "enable": false,                                              #"enable": true to re-enable
            "tags": ["anarchy", "anarchy101", "reddit"]                   #could be empty []
            "html": true                                                  
        }
    }
}
```
