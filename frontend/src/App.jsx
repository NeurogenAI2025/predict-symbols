import React, { useState, useEffect } from 'react';
import './App.css';
import {
  Connection,
  PublicKey,
  SystemProgram,
  Transaction,
} from '@solana/web3.js';
import PhantomLogo from './Phantom.svg';
import NrgLogo from './assets/nrg-logo.svg'; // ✅ nou

const App = () => {
  const [wallet, setWallet] = useState(null);
  const [symbol, setSymbol] = useState('');
  const [availableSymbols, setAvailableSymbols] = useState([]);
  const [days, setDays] = useState(1);
  const [result, setResult] = useState('');
  const [predictionCount, setPredictionCount] = useState(0);
  const [showBuyMenu, setShowBuyMenu] = useState(false);
  const [paymentStatus, setPaymentStatus] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    fetch("http://localhost:8000/symbols")
      .then(res => res.json())
      .then(data => {
        setAvailableSymbols(data.symbols);
        console.log("🔁 Symbols from backend:", data.symbols);
    document.title = "NRG AI Crypto Predictor";
      })
      .catch(err => {
        console.error("❌ Eroare la symbols:", err);
      });
  }, []);

  const handleConnectWallet = async () => {
    if (!window.solana || !window.solana.isPhantom) {
      alert("Phantom Wallet not detected. Please install Phantom extension.");
      window.open('https://phantom.app/', '_blank');
      return;
    }

    try {
      const resp = await window.solana.connect({ onlyIfTrusted: false });
      setWallet(resp.publicKey.toString());
    } catch (err) {
      console.error('Wallet connection error:', err);
    }
  };

  const handleDisconnectWallet = async () => {
    try {
      await window.solana.disconnect();
    } catch {}
    setWallet(null);
  };

  const handlePredict = async () => {
    if (!symbol || days < 1 || days > 7) {
      alert("Please select a valid symbol and a day count between 1 and 7.");
      return;
    }

    setIsLoading(true);
    try {
      const res = await fetch('http://localhost:8000/predict-lstm', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ wallet: wallet || 'anonymous_user', symbol, days }),
      });

      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || err.message);
      }

      const data = await res.json();
      if (data.prediction?.length > 0 || data.prediction?.prediction?.length > 0) {
        const preds = data.prediction.prediction || data.prediction;
        const formatted = preds.map(p => `${p.timestamp}: $${p.Predicted_Price}`).join('\n');
        let extraInfo = "";

        if (data.paid) {
          extraInfo = `✅ Paid plan. Predictions remaining: unlimited`;
        } else if (data.quota?.remaining >= 0) {
          extraInfo = `🧠 Predictions left: ${data.quota.remaining}`;
        }

        setResult(`Predicted price(s) for ${symbol} in ${days} day(s):\n${formatted}\n${extraInfo}`);
        setPredictionCount(prev => prev + 1);
        if (!data.paid && (data.free_predictions_left ?? 0) <= 0) {
          setShowBuyMenu(true);
        }
      } else if (data.message) {
        setResult(`Error: ${data.message}`);
        setShowBuyMenu(true);
      } else {
        setResult('Unexpected response from server.');
      }
    } catch (error) {
      setResult(`Error: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleBuyPlan = async (amount) => {
    if (!wallet) {
      alert('Please connect your wallet to make a purchase.');
      return;
    }

    const recipient = 'G8Gfszz1eXgbLhkLbRD97V9q3QF2Bv8JDGiByT1D2Kzi';
    const solAmount =
      amount === 100 ? 0.01 :
      amount === 500 ? 0.05 :
      amount === 1000 ? 0.08 :
      0.1;

    try {
      const connection = new Connection('https://mainnet.helius-rpc.com/?api-key=d813a643-0ac2-467e-a482-3f0813953003');
      const transaction = new Transaction().add(
        SystemProgram.transfer({
          fromPubkey: new PublicKey(wallet),
          toPubkey: new PublicKey(recipient),
          lamports: solAmount * 1e9,
        })
      );

      transaction.feePayer = new PublicKey(wallet);
      const { blockhash } = await connection.getLatestBlockhash();
      transaction.recentBlockhash = blockhash;

      const signed = await window.solana.signTransaction(transaction);
      const sig = await connection.sendRawTransaction(signed.serialize());

      setPaymentStatus(`✅ Payment sent! TX: https://solscan.io/tx/${sig}`);
      setPredictionCount(0);
      setShowBuyMenu(false);

      await fetch("http://localhost:8000/reset-usage", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ wallet, newLimit: amount }),
      });

    } catch (err) {
      setPaymentStatus('❌ Payment failed: ' + err.message);
    }
  };

  return (
    <div className="app">
      <header>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <img src={NrgLogo} alt="NRG Logo" style={{ width: '40px', height: '40px' }} />
          <h1>NRG Predict</h1>
        </div>
        <div>
          {wallet ? (
            <button onClick={handleDisconnectWallet}>
              <img src={PhantomLogo} alt="Phantom" width="20" style={{ verticalAlign: 'middle', marginRight: '6px' }} />
              Disconnect Wallet
            </button>
          ) : (
            <button onClick={handleConnectWallet}>
              <img src={PhantomLogo} alt="Phantom" width="20" style={{ verticalAlign: 'middle', marginRight: '6px' }} />
              Connect Phantom
            </button>
          )}
        </div>
      </header>

      <main>
        <div className="predict-box">
          <select value={symbol} onChange={(e) => setSymbol(e.target.value)}>
            {availableSymbols.map(sym => (
              <option key={sym} value={sym}>{sym.toUpperCase()}</option>
            ))}
          </select>
          <input
            type="number"
            value={days}
            onChange={(e) => {
              const val = Math.max(1, Math.min(7, Number(e.target.value)));
              setDays(val);
            }}
            placeholder="Days (1-7)"
            min={1}
            max={7}
          />
          <button onClick={handlePredict} disabled={isLoading || !symbol}>
            {isLoading ? 'Loading...' : 'Predict'}
          </button>
          {result && <div className="result"><pre>{result}</pre></div>}
        </div>

        {showBuyMenu && (
          <div className="buy-menu">
            <div>You used all 5 free predictions. Buy more to continue:</div>
            <div className="plans">
              <button onClick={() => handleBuyPlan(100)} className="plan-button">100 Predictions - 0.01 SOL</button>
              <button onClick={() => handleBuyPlan(500)} className="plan-button">500 Predictions - 0.05 SOL</button>
              <button onClick={() => handleBuyPlan(1000)} className="plan-button">1000 Predictions - 0.08 SOL</button>
              <button onClick={() => handleBuyPlan('unlimited')} className="plan-button">Unlimited - 0.1 SOL</button>
            </div>
          </div>
        )}

        {paymentStatus && <div className="payment-status">{paymentStatus}</div>}
      </main>
    </div>
  );
};

export default App;
