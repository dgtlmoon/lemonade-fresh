<img width=256 src="https://raw.githubusercontent.com/dgtlmoon/lemonade-fresh/main/app/static/images/blue-thunder-p7-lemonadestand-expand.jpg">

# Lemonade Fresh - Cryptocurrency Paid Container Provisioner

An extremely simple platform which enables you to host a docker container in exchange for digital currency (bitcoin/litecoin/dogecoin)

*In otherwords* - provision a container using docker-compose when someone pays you with cryptocurrency - host that container for them, accessible as a URL path on your server (that URL path is automatically generated from two random words)

_Yes I'm sure there's a better way todo this, but this works for me :), and it was the fastest way I could get some proof of concept working_

<img src="https://raw.githubusercontent.com/dgtlmoon/lemonade-fresh/main/screenshot.png?large=ok">

# How does it work?

- A person who is interested registers via a simple flask application, the application creates a cryptocurrency payment address, this is emailed and presented to them.
- When a correct payment is detected, a `data/docker-compose-paid-instances.yml` is re-generated with the paid container information (and a container name which is also the container hostname), managed by a simple SQLite DB
- `docker-compose up` runs periodically, it knows when a YAML has changed thanks to its internal checksums, so lazy so implementation.. 
- The new paid container is running, and has a randomly generated hostname, this hostname is available as http://yoursite/random-name via `proxy_pass`

Then the new 'customer' simply accesses their hosted container via nginx's `proxy_pass` as a path on your server, it's recommended to run the containers as a sub-domain, otherwise the nginx rules get a bit complicated ie, https://pay-me.mydomain.io/ , so the hosted container would be available as https://pay-me.mydomain.io/random-name


Some extra bonus stuff happens like
- Generate a salted password and set it as an ENV var so they can login
- [volumes are also created in the docker-compose YAML generator](https://github.com/dgtlmoon/lemonade-fresh/blob/b3d737100c2e94f895c53f7f88b7937a1c3a03e2/app/dcgenerator.py#L30)


# Syncing new containers when paid

```
# m h  dom mon dow   command
*/2 * * * * curl -s https://your-site.com/sync >/dev/null && cd /var/www/provisioner && docker-compose --log-level=WARNING -f docker-compose.yml -f docker-compose.prod.yml -f data/docker-compose-paid-instances.yml  up -d --remove-orphans
```

There's some very lazy things going on here
- Runs every 2 minutes
- `docker-compose.yml` the stock one, required
- `docker-compose.prod.yml` your local settings, like setting the crypto network (`bitcoin`/`testnet`/`litecoin` etc) and return coin address
- `data/docker-compose-paid-instances.yml` the generated extra docker-compose YAML for paid instances

The lazy magic here, is that docker-compose wont do anything unless one of the YAML's change, `up` supports `--remove-orphans` so it's easy to remove containers that are not paid for, and `--log-level=WARNING` keeps it quiet unless something bad happens.

The only shameful thing is that `/sync` call, which re-builds the composer and checks for payments, your nginx shouldnt allow this to be accessed other than locally (or change the code and move it to a local command)

Probably nearly all of this can be removed by using an actual decent interface like coinbase's API, which handles payments way better, but, where is the fun in that? :)


So basically, when someone has paid for their container, a random name is generated (`stir-commuted` herein), and `data/docker-compose-paid-instances.yml` will contain for example...

```
  paid_instance_stir-commuted:
    image: dgtlmoon/changedetection.io:latest
    networks:
    - provisioner_net
    environment:
    - USE_X_SETTINGS=1
    - SALTED_PASS=abc123
    hostname: stir-commuted
    volumes:
    - paid_instance_stir-commuted-data:/datastore
    restart: unless-stopped

```

And they can access it via https://yoursite.com/stir-commuted via [this nginx location statement](https://github.com/dgtlmoon/lemonade-fresh/blob/2c2443601a53e14007aca0185320b71e00d59bdd/config/nginx/default.conf#L32)

`image:` is set by `HOSTED_IMAGE` env var

## Testing/Development

- I like the [Electrum client](https://electrum.org/), start it in _testnet_ mode, `electrum --testnet`
- Use https://testnet-faucet.com/btc-testnet/ or a similar "test coin faucet" to get some test-coins (remember to return them when you're done!)
- It's good to set the return address for the coins back to your wallet (dont store them on the server! See `BTC_FORWARD_ADDRESS` env var)

## Batteries NOT included

- Some web-ops stuff like `certbot` not included, you will need to sort out how this works.
- No threaded python gunicorn etc server
