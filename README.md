<img width=256 src="https://raw.githubusercontent.com/dgtlmoon/lemonade-fresh/main/app/static/images/blue-thunder-p7-lemonadestand-expand.jpg">

# Lemonade Fresh - Cryptocurrency Paid Container Provisioner

An extremely simple platform which enables you to earn digital currency for docker containers as a service (CaaS/SaaS)

In otherwords - provision a container using docker-compose when someone pays you with cryptocurrency - host that container for them.

_Yes I'm sure there's a better way todo this, but this works for me :), and it was the fastest way I could get some proof of concept working_

<img width="100%" src="https://raw.githubusercontent.com/dgtlmoon/lemonade-fresh/main/screenshot.png">

# How does it work?

- A person who is interested registers via a simple flask application, the application creates a cryptocurrency payment address, this is emailed and presented to them.
- When a correct payment is detected, a `data/docker-compose-paid-instances.yml` is re-generated with the paid container information (and a container name which is also the container hostname), managed by a simple SQLite DB
- `docker-compose up` runs periodically, it knows when a YAML has changed thanks to its internal checksums, so lazy so implementation.. 
- The new paid container is running, and has a randomly generated hostname, this hostname is available as http://yoursite/random-name via `proxy_pass`

Some extra bonus stuff happens like
- Generate a salted password and set it as an ENV var so they can login
- [volumes are also created in the docker-compose YAML generator](https://github.com/dgtlmoon/lemonade-fresh/blob/b3d737100c2e94f895c53f7f88b7937a1c3a03e2/app/dcgenerator.py#L30)


## Testing/Development

- I like the [Electrum client](https://electrum.org/), start it in _testnet_ mode, `electrum --testnet`
- Use https://testnet-faucet.com/btc-testnet/ or a similar "test coin faucet" to get some test-coins (remember to return them when you're done!)
- It's good to set the return address for the coins back to your wallet (dont store them on the server! See `BTC_FORWARD_ADDRESS` env var)

## Batteries NOT included

- Some web-ops stuff like `certbot` not included, you will need to sort out how this works.
- No threaded python gunicorn etc server
