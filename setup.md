# Setup

## Requirements
Docker、Mongodb、[Imageproxy](ghcr.io/willnorris/imageproxy)

## Required Environ Variables
General  
`app_secret_key` -> flask app secrect key  
`DATABASE_URL` -> url for database  
`MAIL_SERVER` -> mailserver addr  
`MAIL_DEFAULT_SENDER` -> mail sender  
`MAIL_USERNAME` -> mailserver username  
`email_key` -> emailserver passwd  
Discord  
`DISCORD_OAUTH_CLIENT_ID` -> Discord OAUTH client id  
`DISCORD_OAUTH_CLIENT_SECURITE` -> Discord OAUTH client secret  
`DISCORD_OAUTH_TOKEN` ->  Discord OAUTH TOKEN  
`DISCORD_OAUTH_REDIRECT_URL` -> Discord redirect url (callback url)
`DISCORD_OAUTH_AUTH_URL` -> Discord oauth auth url (startwith:https://discord.com/oauth2/authorize)



## Commands
```
git clone https://github.com/yoni13/SGGS-ANON/
cd SGGS-ANON
docker build -t sggsanon:latest .
docker run -d --name sggsanon -p <host-port>:5000 sggsanon:latest
```
