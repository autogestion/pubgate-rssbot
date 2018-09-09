## PubGate RSSBot
Extension for [PubGate](https://github.com/autogestion/pubgate), federates rss-feeds

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
/api/v1/auth  POST
```
payload
```
{
	"username": "user",
	"password": "pass",
	"actor_type": "Service",
	"email": "admin@mail.com",                                     #optional
	"invite": "xyz",                                               #required if register by invite enabled
	"details": {
		"rssbot": {
			"feed": "https://www.reddit.com/r/Anarchy101/.rss",
			"enable": true,
			"tags": ["anarchy", "anarchy101", "reddit"]       #could be empty []
			"html": false                                     #if feed provides content as html, title will be used
		}
	}
}
```

#### Disable/Update bot
```
/rssbot/<username>  UPDATE   (auth required)
```
payload
```
{
    "feed": "https://www.reddit.com/r/Anarchy101/.rss",           #change to update
    "enable": false,                                              #"enable": true to re-enable
    "tags": ["anarchy", "anarchy101", "reddit"]                   #could be empty []
    "html": true                                                  #could be switched to true to federate html-formatted content
}
```
