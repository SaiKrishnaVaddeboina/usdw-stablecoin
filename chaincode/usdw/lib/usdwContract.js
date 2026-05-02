'use strict';
const { Contract } = require('fabric-contract-api');

class USDwContract extends Contract {
  _accountKey(id){ return `acct:${id}`; }
  _getMSPId(ctx){ const cid = ctx.clientIdentity; return cid.getMSPID ? cid.getMSPID() : 'UnknownMSP'; }
  async _readJSON(ctx, key){ const b = await ctx.stub.getState(key); if(!b||!b.length) return null; try{return JSON.parse(b.toString());}catch(e){return null;} }
  async _writeJSON(ctx, key, obj){ await ctx.stub.putState(key, Buffer.from(JSON.stringify(obj))); }
  async _readAccount(ctx, id){ const a = await this._readJSON(ctx, this._accountKey(id)); if(!a) throw new Error(`Account ${id} not found`); return a; }
  async _getSupply(ctx){ const v = await this._readJSON(ctx, 'SUPPLY'); return v&&v.value? BigInt(v.value):0n; }
  async _setSupply(ctx, s){ await this._writeJSON(ctx, 'SUPPLY', { value: s.toString() }); }
  async _getReserves(ctx){ const v = await this._readJSON(ctx, 'RESERVES'); return v&&v.value? BigInt(v.value):0n; }

  async RegisterAccount(ctx, id){
    const key = this._accountKey(id);
    const ex = await ctx.stub.getState(key);
    if(ex && ex.length>0) return `Account ${id} already exists`;
    const acct = { id, ownerMSP: this._getMSPId(ctx), kycStatus:'PENDING', frozen:false, sanctioned:false, balance:'0', meta:{} };
    await this._writeJSON(ctx, key, acct);
    await ctx.stub.setEvent('AccountRegistered', Buffer.from(JSON.stringify({accountId:id})));
    return `Account ${id} registered`;
  }
  async SubmitKYC(ctx, id, kycHash){
    const a = await this._readAccount(ctx, id);
    a.kycHash = kycHash; a.kycStatus='SUBMITTED';
    await this._writeJSON(ctx, this._accountKey(id), a);
    await ctx.stub.setEvent('KYCUploaded', Buffer.from(JSON.stringify({accountId:id})));
    return `KYC submitted for ${id}`;
  }
  async VerifyKYC(ctx, id){
    const a = await this._readAccount(ctx, id);
    a.kycStatus='VERIFIED';
    await this._writeJSON(ctx, this._accountKey(id), a);
    await ctx.stub.setEvent('KYCVerified', Buffer.from(JSON.stringify({accountId:id})));
    return `KYC verified for ${id}`;
  }
  async FreezeAccount(ctx, id){
    const a = await this._readAccount(ctx, id);
    if(a.frozen) return `Account ${id} already frozen`;
    a.frozen=true; await this._writeJSON(ctx, this._accountKey(id), a);
    await ctx.stub.setEvent('AccountFrozen', Buffer.from(JSON.stringify({accountId:id})));
    return `Account ${id} frozen`;
  }
  async UnfreezeAccount(ctx, id){
    const a = await this._readAccount(ctx, id);
    if(!a.frozen) return `Account ${id} is already unfrozen`;
    a.frozen=false; await this._writeJSON(ctx, this._accountKey(id), a);
    await ctx.stub.setEvent('AccountUnfrozen', Buffer.from(JSON.stringify({accountId:id})));
    return `Account ${id} unfrozen`;
  }
  async SanctionAccount(ctx, id){
    const a = await this._readAccount(ctx, id);
    a.sanctioned=true; await this._writeJSON(ctx, this._accountKey(id), a);
    await ctx.stub.setEvent('AccountSanctioned', Buffer.from(JSON.stringify({accountId:id})));
    return `Account ${id} sanctioned`;
  }
  async UnsanctionAccount(ctx, id){
    const a = await this._readAccount(ctx, id);
    a.sanctioned=false; await this._writeJSON(ctx, this._accountKey(id), a);
    await ctx.stub.setEvent('AccountUnsanctioned', Buffer.from(JSON.stringify({accountId:id})));
    return `Account ${id} unsanctioned`;
  }
  async SetReserveReport(ctx, amountStr){
    const msp = this._getMSPId(ctx);
    if(msp!=='Org1MSP') throw new Error('Only issuer (Org1MSP) may set reserves');
    const amt = BigInt(amountStr);
    await this._writeJSON(ctx, 'RESERVES', { value: amt.toString(), by:msp, ts: ctx.stub.getTxTimestamp() });
    await ctx.stub.setEvent('ReserveUpdated', Buffer.from(JSON.stringify({reserves:amt.toString()})));
    return `Reserves set to ${amt}`;
  }
  async Mint(ctx, toId, amountStr){
    const msp = this._getMSPId(ctx);
    if(msp!=='Org1MSP') throw new Error('Only issuer (Org1MSP) may mint');
    const amount = BigInt(amountStr);
    if(amount<=0n) throw new Error('Mint amount must be positive');
    const supply = await this._getSupply(ctx);
    const reserves = await this._getReserves(ctx);
    const newSupply = supply + amount;
    if(newSupply>reserves) throw new Error('Mint blocked: reserves would be below total supply');
    const to = await this._readAccount(ctx, toId);
    if(to.kycStatus!=='VERIFIED') throw new Error('Recipient must be KYC-VERIFIED');
    if(to.frozen || to.sanctioned) throw new Error('Recipient is frozen or sanctioned');
    to.balance=(BigInt(to.balance)+amount).toString();
    await this._writeJSON(ctx, this._accountKey(toId), to);
    await this._setSupply(ctx, newSupply);
    await ctx.stub.setEvent('Mint', Buffer.from(JSON.stringify({to:toId, amount:amount.toString(), supply:newSupply.toString()})));
    return `Minted ${amount} to ${toId}`;
  }
  async Transfer(ctx, fromId, toId, amountStr, travelRuleHash=''){
    const amount = BigInt(amountStr);
    if(amount<=0n) throw new Error('Amount must be positive');
    const from = await this._readAccount(ctx, fromId);
    const to = await this._readAccount(ctx, toId);
    if(from.kycStatus!=='VERIFIED' || to.kycStatus!=='VERIFIED') throw new Error('KYC not verified for sender or recipient');
    if(from.frozen || to.frozen) throw new Error('One of the accounts is frozen');
    if(from.sanctioned || to.sanctioned) throw new Error('Transfer blocked: sanctioned party');
    if(BigInt(from.balance) < amount) throw new Error('Insufficient balance');
    from.balance=(BigInt(from.balance)-amount).toString();
    to.balance=(BigInt(to.balance)+amount).toString();
    await this._writeJSON(ctx, this._accountKey(fromId), from);
    await this._writeJSON(ctx, this._accountKey(toId), to);
    const ev = { type:'USDwTransfer', from:fromId, to:toId, amount:amount.toString(), travelRuleHash, ts: ctx.stub.getTxTimestamp(), txId: ctx.stub.getTxID() };
    await ctx.stub.setEvent('Transfer', Buffer.from(JSON.stringify(ev)));
    return `Transferred ${amount} from ${fromId} to ${toId}`;
  }
  async GetAccount(ctx, id){ const a = await this._readAccount(ctx, id); return JSON.stringify(a); }
  async TxHistory(ctx, id){
    const it = await ctx.stub.getHistoryForKey(this._accountKey(id));
    const out = []; for await (const r of it){ out.push({txId:r.txId, ts:r.timestamp, isDelete:r.isDelete, value:r.value? r.value.toString():null}); }
    return JSON.stringify(out);
  }
}

module.exports = USDwContract;
