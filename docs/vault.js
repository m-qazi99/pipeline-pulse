/* The import boundary is shared by the browser vault and its Node tests. */
(function(root){
  'use strict';
  const fields=['pipeline','inject','failure_count','repair','concurrency','retries','backoff','deadline','challenge'];
  function normalize(value){
    if(!value||typeof value!=='object'||Array.isArray(value))throw new Error('Import a JSON experiment object.');
    const input=value.input||value;
    if(!input||typeof input!=='object'||typeof input.pipeline!=='string')throw new Error('The experiment needs a pipeline definition.');
    if(input.pipeline.length>2000000)throw new Error('Pipeline definition exceeds 2 MB.');
    let nodes;try{nodes=JSON.parse(input.pipeline);}catch{throw new Error('Pipeline definition is invalid JSON.');}
    if(!Array.isArray(nodes)||nodes.length<1||nodes.length>40||nodes.some(n=>!n||typeof n!=='object'||typeof n.id!=='string'))throw new Error('Use 1–40 nodes with text IDs.');
    const output={workspace:'studio'};
    for(const key of fields)if(Object.hasOwn(input,key)){
      const v=input[key];if(typeof v!=='string'&&typeof v!=='number')throw new Error('Invalid value for '+key+'.');
      if(typeof v==='number'&&!Number.isFinite(v))throw new Error('Invalid number for '+key+'.');
      if(typeof v==='string'&&v.length>2000000)throw new Error('Field exceeds 2 MB.');
      output[key]=v;
    }
    return output;
  }
  const api={normalize};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;
  else root.PulseVault=api;
})(typeof window!=='undefined'?window:{});
