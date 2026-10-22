# Résolution Maths

Application éducative de résolution mathématique pour la préparation du baccalauréat à Madagascar. Version **1.1.1**.

## Fonctionnement

L'élève sélectionne le **domaine mathématique**, saisit lui-même ses données, puis obtient un résultat symbolique avec les étapes pertinentes. Les modes prévus dans cette première version : équations et inéquations en `x`, simplification, développement, factorisation, dérivation et tangente, primitives et intégrales, limites, étude de fonction, systèmes, suites récurrentes, statistiques, complexes, PGCD/PPCM, loi binomiale, intérêts simples et composés.

**Important :** il ne s'agit pas d'une IA conversationnelle ni d'un interprète universel des énoncés rédigés. Les champs guidés sont conçus pour les notations des exercices du BAC. Les contenus et méthodes ne prétendent pas couvrir tous les problèmes et toutes les séries, ni remplacer les démonstrations d'un enseignant.

## Dérivation et lisibilité

- Dérivées exactes d’ordre 1 à 5, avec racines imbriquées, produits, quotients, logarithmes, exponentielles et fonctions trigonométriques.
- Explication de la dérivée intérieure des racines composées et de la règle du quotient ou du produit.
- Fractions verticales, radicaux et logarithme `ln` en mode d’affichage mathématique. Les puissances demi-entières sont présentées avec une racine : `(x²+1)√(x²+1)` au lieu d’un exposant `3/2`. Le changement est typographique et ne force aucune identité de racines.
- Domaine réel de la saisie et domaine de validité de chaque dérivée, avec la notation scolaire française `]a ; b[`. Les restrictions d’un dénominateur ou d’une racine sont conservées après simplification.
- Les tangentes utilisent toujours la première dérivée. Elles sont refusées hors du domaine réel ou en un point où une dérivée réelle bilatérale finie n’a pas été établie. Par exemple, `sqrt(x^2)` donne `|x|` et n’est pas dérivable en zéro.
- Contrôle indépendant par différences finies en quatre points au maximum, choisis dans le domaine. Une concordance numérique locale n’est pas une preuve ; si le contrôle n’est pas concluant, l’application l’indique.
- L’étude de fonction utilise le même calcul de dérivée et les mêmes restrictions de domaine. Un domaine non déterminé n’est jamais remplacé arbitrairement par tous les réels.

Exemples à essayer dans « Dérivées » : `sqrt(x^2+1)`, `sqrt(x+1)/x`, `sqrt(sqrt(x)+1)`, `sqrt(x^2)` et `ln(x)/x^2`. Le symbole `√(x)` est également accepté. Le bouton racine peut entourer une expression sélectionnée.

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

## Application Android (APK)

Une application Android native est disponible dans `android/` : elle embarque l’interface,
Pyodide, SymPy et KaTeX. Les calculs et les formules sont utilisables **hors connexion,
dès le premier démarrage**. Android 8.0 ou plus récent est requis, avec un Android System
WebView à jour. Le nom dans le téléphone est **Résolution Maths** et l’icône reprend le
symbole √x du site. L’historique reste uniquement sur l’appareil.

Le contenu local utilise une origine HTTPS interceptée dans la WebView, pour permettre
les workers et WebAssembly sans autoriser les URL `file://` ni exposer de pont JavaScript
vers Android. Toutes les dépendances sont incluses dans le fichier APK. Les requêtes
externes de la WebView sont bloquées. Les barres système, les encoches et le clavier sont
pris en compte par la fenêtre Android.

La compilation nécessite Java 17, Python 3, le SDK `platforms;android-35` et
`build-tools;35.0.0`. Seule la compilation télécharge les dépendances. La clé de signature
est privée : elle doit être conservée avec son mot de passe pour les futures mises à jour.

```bash
export ANDROID_SDK_ROOT=/chemin/vers/android-sdk
export ANDROID_KEYSTORE_PASSWORD='mot-de-passe-de-la-cle'
export ANDROID_KEY_PASSWORD="$ANDROID_KEYSTORE_PASSWORD"
python scripts/build_android.py --keystore /chemin/prive/resolutionmaths.p12
```

Le fichier généré est `dist/Resolution-Maths-1.1.1.apk`. Ne jamais publier la clé privée
dans le dépôt. Le workflow **APK Android de test** fournit aussi un APK de test dans les
artifacts GitHub Actions. Celui-ci s’installe comme une application séparée nommée
**Résolution Maths Test** : sa clé temporaire ne sert pas à signer les mises à jour de
l’application distribuée. Une nouvelle compilation de test peut nécessiter de désinstaller
la précédente application de test ; la version distribuée et son historique restent séparés.

### Icône de la version 1.1.1

Le logo √x utilise des ressources dédiées à Résolution Maths. Les anciennes ressources
`ic_launcher` ont été retirées. L’APK inclut les icônes PNG dans cinq résolutions pour
les installateurs, les versions adaptatives ronde et standard et une couche monochrome
pour les icônes thématiques d’Android 13 et plus. Le logo du site et celui de l’application
utilisent le même dessin. Pour régénérer les ressources : installer Pillow puis exécuter
`python scripts/generate_android_icons.py`.

Le nom de package et la clé de signature de la version distribuée sont conservés.
La version Android passe de 110 à 111 pour permettre la mise à jour directe. Après la
mise à jour, si un raccourci d’accueil conserve l’ancienne image dans son cache, retirer
uniquement ce raccourci puis le recréer depuis la liste des applications.

## Notation

| Opération | Saisie |
| --- | --- |
| Équation | `2x^2-5x+2=0` |
| Inéquation | `x^2-5x+6<=0` |
| Système | `2x+y=5; x-y=1` |
| Dérivée avec racine | `sqrt(x^2+1)` ou `√(x^2+1)` |
| Dérivée seconde | `x/sqrt(x^2+1)`, ordre `2` |
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
- Les domaines de certaines expressions transcendantes restent indéterminés. Le domaine de dérivation affiché est alors limité aux intervalles effectivement établis ; les fonctions discontinues et la dérivation au sens des distributions ne sont pas prises en charge.
- Un calcul lent est interrompu au bout de 25 secondes dans l'interface (worker recréé).
- Pour un vrai déploiement hors connexion, héberger Pyodide/SymPy et KaTeX localement et étendre la stratégie de cache. Ne pas promettre le hors-ligne avant ces tests.
- Les suites de tests actuelles sont des tests représentatifs, pas une validation de toutes les annales malgaches.

## Confidentialité

Aucune inscription, publicité, analytique ou API de calcul distante. Le navigateur télécharge Pyodide et KaTeX depuis jsDelivr (ce fournisseur voit les requêtes de téléchargement selon sa propre politique). L'historique reste local au navigateur, est effaçable depuis l'application et peut être supprimé avec les données du site.

## Licence

Le code est placé sous licence MIT, voir `LICENSE`.
