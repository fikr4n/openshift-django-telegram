This is really a short explanation. Please be patient.

## Initial setup

Set required environment variables:

- `DJANGO_DEBUG=true|false`
- `DJANGO_SECRET_KEY=django_random_secret`
- `OBIWAN_TELEGRAM_TOKEN=bot_token_from_botfather`

User's environment variables in OpenShift can be set by creating files like this:

```
echo -n false > $OPENSHIFT_HOMEDIR/.env/user_vars/DJANGO_DEBUG
echo -n 'xxxxx' > $OPENSHIFT_HOMEDIR/.env/user_vars/DJANGO_SECRET_KEY
echo -n '1234:xxxxx' > $OPENSHIFT_HOMEDIR/.env/user_vars/OBIWAN_TELEGRAM_TOKEN
```

Set required database records in table `Misc`:

- `valid_access_token` - random token to authenticate Telegram request to our web service
- `my_user_id` - user ID of the bot

Register webhook:

```
curl 'https://api.telegram.org/bot${OBIWAN_TELEGRAM_TOKEN}/setWebhook' \
 --data 'url=https%3A%2F%2F${ADDRESS_OR_DOMAIN}%2Fupdate%2F%3Fauth%3D${valid_access_token}'
```

The `${variable}` above should be replaced directly with the correct values, because single
quoted string will not be expanded by the shell.