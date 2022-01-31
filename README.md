<img src="docs/images/lemonade.png">

# LemonadeStand Provisioner

An extremely simple platform which enables you to earn money/digital currency for hosting software as a service (SaaS)

_Yes I'm sure there's a better way todo this, but this works for me :)_

```
docker-compose -f docker-compose.yml -f data/docker-compose-paid-instances.yml up
```

## Testing


- I like the [Electrum client](https://electrum.org/), start it in _testnet_ mode, `electrum --testnet`
- Use https://testnet-faucet.com/btc-testnet/ or a similar "test coin faucet" to get some test-coins (remember to return them when you're done!)
- It's good to set the return address for the coins back to your wallet (dont store them on the server!)
- ./venv/bin/cli-wallet
