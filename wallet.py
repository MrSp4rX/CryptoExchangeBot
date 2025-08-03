from bip_utils import Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes
from bitcoinlib.wallets import Wallet
from web3 import Web3
import os
from bip_utils import Bip39MnemonicGenerator, Bip39SeedGenerator, Bip44, Bip44Coins

def generate_wallets():
    mnemonic = Bip39MnemonicGenerator().FromWordsNumber(12).ToStr()
    seed_bytes = Bip39SeedGenerator(mnemonic).Generate()
    eth_wallet = Bip44.FromSeed(seed_bytes, Bip44Coins.ETHEREUM).DeriveDefaultPath()
    btc_wallet = Bip44.FromSeed(seed_bytes, Bip44Coins.BITCOIN).DeriveDefaultPath()
    eth_address = eth_wallet.PublicKey().ToAddress()
    btc_address = btc_wallet.PublicKey().ToAddress()
    return mnemonic, btc_address, eth_address

# Update your wallet.py file - replace the get_eth_balance function with this:

def get_eth_balance(address, infura_url):
    """Get ETH balance for an address"""
    try:
        from web3 import Web3
        w3 = Web3(Web3.HTTPProvider(infura_url))
        if not w3.is_connected():
            raise Exception("Failed to connect to Ethereum network")
        if not Web3.is_address(address):
            raise Exception("Invalid Ethereum address")
        balance_wei = w3.eth.get_balance(address)
        balance_eth = Web3.from_wei(balance_wei, 'ether')
        return float(balance_eth)
    except Exception as e:
        print(f"Error getting ETH balance: {str(e)}")
        return 0.0

def gget_eth_balance(address, web3_url):
    w3 = Web3(Web3.HTTPProvider(web3_url))
    balance_wei = w3.eth.get_balance(address)
    return w3.fromWei(balance_wei, 'ether')

def get_btc_balance(address):
    from bitcoinlib.services.services import Service
    svc = Service(network='bitcoin')
    info = svc.getbalance(address)
    return info['confirmed'] / 1e8 if info and 'confirmed' in info else 0

def send_eth(private_key, to_address, amount, web3_url):
    w3 = Web3(Web3.HTTPProvider(web3_url))
    account = w3.eth.account.privateKeyToAccount(private_key)
    nonce = w3.eth.get_transaction_count(account.address)
    tx = {
        'nonce': nonce,
        'to': to_address,
        'value': w3.toWei(amount, 'ether'),
        'gas': 21000,
        'gasPrice': w3.toWei('50', 'gwei'),
    }
    signed = w3.eth.account.sign_transaction(tx, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    return tx_hash.hex()
