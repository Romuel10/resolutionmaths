# Résolution Maths

Application éducative de résolution mathématique pour la préparation du baccalauréat à Madagascar. Version **1.0.0**.

## Fonctionnement

L'élève sélectionne le **domaine mathématique**, saisit lui-même ses données, puis obtient un résultat symbolique avec les étapes pertinentes. Les modes prévus dans cette première version : équations et inéquations en `x`, simplification, développement, factorisation, dérivation et tangente, primitives et intégrales, limites, étude de fonction, systèmes, suites récurrentes, statistiques, complexes, PGCD/PPCM, loi binomiale, intérêts simples et composés.

**Important :** il ne s'agit pas d'une IA conversationnelle ni d'un interprète universel des énoncés rédigés. Les champs guidés sont conçus pour les notations des exercices du BAC. Les contenus et méthodes ne prétendent pas couvrir tous les problèmes et toutes les séries, ni remplacer les démonstrations d'un enseignant.

## Architecture

- Frontend accessible : HTML, CSS et JavaScript natif, sans processus de build.
- Moteur : **SymPy**, exécuté directement sur l'appareil via **Pyodide** dans un Web Worker.
- Affichage mathématique : KaTeX (CDN), avec repli en texte brut si non disponible.
- Historique : 20 dernières résolutions dans `localStorage`, jamais envoyées sur un serveur applicatif.
- Courbes : canvas, aperçu numérique séparé des conclusions symboliques.
- PWA : manifeste + service worker pour les ressources locales. **Le premier chargement nécessite Internet**, et l'utilisation intégralement hors connexion du moteur Pyodide et de KaTeX n'est pas garantie (les ressources tierces CDN ne sont pas précachées par le service worker).

Le moteur Pyodide est figé en version `0.29.5`. Les versions peuvent être mises à jour avec des tests de non-régression.

## Installer / tester en local

```bash
python -m http.server 8080
```

Puis ouvrir `http://localhost:8080` dans un navigateur récent. N'ouvrez pas directement le fichier HTML avec `file://`, qui empêche le Worker et le chargement du moteur.

```bash
python -m pip install sympy==1.14.0 pytest
python -m pytest -q
node --check app.js
```

## Déployer sur Netlify

1. Connecter le dépôt GitHub à Netlify.
2. Laisser la commande de build vide. `netlify.toml` configure le répertoire publié à `.`.
3. Déployer et tester la première résolution avec une connexion Internet.
4. Pour une installation sur Android, ouvrir le site dans Chrome puis utiliser « Installer l'application » selon les options du navigateur.

## Notation

| Opération | Saisie |
| --- | --- |
| Équation | `2x^2-5x+2=0` |
| Inéquation | `x^2-5x+6<=0` |
| Système | `2x+y=5; x-y=1` |
| Dérivée | `x^3-3x^2+2` |
| Suite récurrente | `(u+3)/4`, u₀ `5`, termes `6` |
| Statistiques | `10; 12; 15; 18` |
| Complexe | `3+4i` |
| Probabilité | nombre d'essais `10`, succès `3`, probabilité `0.5` |

## Limites connues et exigences de qualité

- L'application ne traite pas les consignes générales en langue naturelle. Les modules sont spécifiques.
- Les équations sont résolues sur les **réels** dans le mode équation ; le module complexes traite un nombre complexe connu, pas encore une équation dans ℂ.
- Les résultats exacts peuvent être fournis sous forme d'ensembles symboliques ou conditionnels lorsque SymPy ne trouve pas de forme fermée.
- Les fonctions discontinues, certaines intégrales impropres, inéquations transcendantales et cas très complexes nécessitent une vérification manuelle.
- Les études de fonctions ne produisent pas encore les tableaux de signes/variations scolaires complets.
- Un calcul lent est interrompu au bout de 25 secondes dans l'interface (worker recréé).
- Pour un vrai déploiement hors connexion, héberger Pyodide/SymPy et KaTeX localement et étendre la stratégie de cache. Ne pas promettre le hors-ligne avant ces tests.
- Les suites de tests actuelles sont des tests représentatifs, pas une validation de toutes les annales malgaches.

## Confidentialité

Aucune inscription, publicité, analytique ou API de calcul distante. Le navigateur télécharge Pyodide et KaTeX depuis jsDelivr (ce fournisseur voit les requêtes de téléchargement selon sa propre politique). L'historique reste local au navigateur, est effaçable depuis l'application et peut être supprimé avec les données du site.

## Licence

Le code est placé sous licence MIT, voir `LICENSE`.
