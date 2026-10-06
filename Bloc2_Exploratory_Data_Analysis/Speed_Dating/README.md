# Speed Dating (Tinder) : qu'est-ce qui pousse à dire oui ?

Lien GitHub du projet : https://github.com/sandrinehardy/mes_projets_jedha_dsft36/tree/main/Bloc2_Exploratory_Data_Analysis/Speed_Dating

## Objectif

Tinder veut mieux comprendre ce qui donne envie d'avoir un second rendez-vous avec quelqu'un. Le projet analyse des soirées de speed dating (rendez-vous de 4 minutes) : après chaque rendez-vous, les participants ont noté leur partenaire et décidé de le revoir ou non, et des questionnaires donnent des informations sur eux-mêmes.

## Données

8 378 rendez-vous et 195 colonnes (`Speed+Dating+Data.csv`), avec le dictionnaire des colonnes (`Speed+Dating+Data+Key.doc`). Après nettoyage, l'analyse porte sur 449 participants : quatre soirées dont les préférences déclarées ne sont pas comparables à celles des autres sont écartées.

## Questions étudiées

1. Quels sont les attributs les moins désirables chez un partenaire, pour les hommes et pour les femmes ?
2. Quelle importance les gens accordent-ils à l'attractivité, par rapport à son impact réel ?
3. Les intérêts communs sont-ils plus importants qu'une origine commune ?
4. Les gens peuvent-ils prédire avec justesse leur propre valeur sur le marché des rencontres ?
5. Vaut-il mieux être le premier rendez-vous de la soirée ou le dernier ?
6. Qu'est-ce qui fait dire oui ?

## Résultats

- Le oui dépend d'abord de l'attractivité (corrélation de 0,48 avec la décision), du fun (0,42) et des intérêts communs ressentis (0,41). La sincérité, l'intelligence et l'ambition comptent beaucoup moins (0,18 à 0,23).
- Les hommes disent oui plus souvent que les femmes (45,5 % contre 37,9 %). Seulement 16,5 % des rendez-vous sont des matchs, car il faut deux oui.
- Ce que les gens disent chercher ne correspond pas à ce qu'ils font : avant la soirée, les femmes valorisent l'intelligence et la sincérité, mais ce sont l'attractivité, le fun et les intérêts communs qui pèsent dans leurs décisions.
- Les intérêts communs ressentis comptent beaucoup plus que l'origine commune (corrélation de 0,41 contre 0,03).
- Les gens se surestiment d'environ 1 point sur 10.
- L'ordre de passage joue très peu : un petit avantage pour le premier rendez-vous (49 % de oui contre 42 % en moyenne).

Limites : petit échantillon (449 étudiants d'une même université), rendez-vous de 4 minutes en face à face différent d'un swipe, corrélations qui ne prouvent pas des causes.

## Fichiers

- `SHY_Speed_Dating_bloc_2.ipynb` : notebook complet (préparation, statistiques descriptives, six questions, conclusion)
- `Speed+Dating+Data.csv` : données
- `Speed+Dating+Data+Key.doc` : dictionnaire des colonnes
