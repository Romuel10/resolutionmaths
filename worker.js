/* Le moteur s'exécute dans un Web Worker pour garder l'interface réactive.
 * Version figée : changer de version Pyodide demande de refaire les tests.
 */
const CDN = 'https://cdn.jsdelivr.net/pyodide/v0.29.5/full/';
let loadingPromise;
function status(message,state=''){self.postMessage({type:'status',message,state});}
async function init(){
  status('Téléchargement du moteur…');
  importScripts(CDN+'pyodide.js');
  const pyodide=await loadPyodide({indexURL:CDN});
  status('Chargement du calcul symbolique…');
  await pyodide.loadPackage('sympy');
  const source=await fetch('./solver.py').then(r=>{if(!r.ok)throw new Error('Le moteur mathématique est introuvable.');return r.text();});
  await pyodide.runPythonAsync(source);
  status('Moteur prêt','ready');
  return pyodide;
}
self.onmessage=async event=>{
  const {id,type,payload}=event.data||{};
  if(type!=='solve')return;
  try{
    loadingPromise??=init().catch(error=>{loadingPromise=undefined;throw error;});
    const pyodide=await loadingPromise;
    pyodide.globals.set('payload_json',JSON.stringify(payload));
    let response;
    try{response=await pyodide.runPythonAsync('solve_json(payload_json)');}
    finally{pyodide.globals.delete('payload_json');}
    self.postMessage({id,type:'result',payload:JSON.parse(response)});
  }catch(error){
    self.postMessage({id,type:'error',error: String(error?.message||'Impossible de calculer.')});
    status('Moteur indisponible','error');
  }
};
