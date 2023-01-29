```html
<!DOCTYPE html>
<html>
<head>
  <script src="https://cdn.jsdelivr.net/pyodide/v0.22.1/full/pyodide.js"></script>
</head>
<body>
  <h1>Pyodide Example</h1>
</body>
</html>
```
```js
async function main(){
  let pyodide = await loadPyodide();
  await pyodide.loadPackage("micropip");
	const micropip = pyodide.pyimport("micropip");
  await micropip.install('beautifulsoup4');
  await micropip.install('cevlib==2.0.3');
  const cache = await pyodide.runPythonAsync(`
from js import Object
from pyodide.ffi import to_js
from cevlib.match import Match
match = await Match.byUrl("https://championsleague.cev.eu/en/match-centres/cev-champions-league-volley-2023/cev-champions-league-volley-2023-men/clvm-43-berlin-recycling-volleys-v-aluron-cmc-warta-zawiercie/")
await match.init()
cache = await match.result()
to_js(cache.toJson())
`);
console.log(cache)
}
main();
```
- Remove threads (asyncRunInThread)
- implement in cev-next
- host on github pages
