# FoodBot
FoodBot is a SlackBot for aggregating restarant menus and posting them when wanted.
Currently hardcoded to support only a single restaurant: The Arrendondo Café in the University of Florida.

This is unversioned as no releases are planned.

## Features
* Café web scraping via Beautiful Soup and formatting
* Food name to Emoji (hardcoded list)
* Slack output

## Example Output

![Imgur](https://i.imgur.com/lLo9dyN.png)

## Installing and Running

All dependencies are provided by pip

```
pip -r requirements.txt
```

Then all you need to run is

```
python foodbot.py yourconfig.json
```

This will load `yourconfig.json` or `config.json` if no argument was specified.

## Configuration
Below is a description of the configuration options available for this bot

### Top-Level
| Field          | Type                | Description  |
| ---------------|---------------------|--------------|
| `testing`      | Boolean             | Places the bot in to test mode, meaning it will not send to Slack |
| `servers`      | Array[Server Item]  | The Slack servers to broadcast to |

### Server Item
| Field         | Type        | Description  |
| ------------- |-------------|--------------|
| `name`        | String      | A helpful name for the Slack server entry |
| `username`    | Integer     | What username the Slack bot should have |
| `channel`     | String      | The channel within the Slack server to broadcast to |
| `admin`       | String      | The admin user where test or error messages should be sent |
| `url`         | String      | The Slack API URL with secrets |

### Example configuration

Here's an example configuration:

```javascript
{
  "testing" : true,
  "servers" : [
    {
      "name" : "Slack Name",
      "username" : "FoodBot",
      "channel" : "#somechannel",
      "admin" : "@yourname",
      "url" : "https://hooks.slack.com/services/your_webhook_rl"
    }
  ]
}
```

## License
Unlicensed and free to use for everyone (public domain).
