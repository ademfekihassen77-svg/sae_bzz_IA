# README – Stratégie de l’IA



Nom de l’IA : FEKIHASSEN\_GIRARD



Auteurs : Alexandre Girard / Adem Feki Hassen



Groupe : INF1-A



Présentation du projet



Ce projet correspond à la SAE 1.02.





##### 1\. Objectif général de l’IA



L’objectif de cette intelligence artificielle est de maximiser la récolte de nectar tout en assurant une défense minimale contre les adversaires.

La stratégie repose sur une répartition des rôles entre les différents types d’abeilles et une gestion progressive de la partie (début, milieu, fin).



##### 2\. Stratégie de ponte des abeilles



La fonction ponte adapte le type d’abeille créé en fonction :



* du nectar disponible,
* du nombre d’abeilles déjà présentes,
* du moment de la partie.

###### 

###### Début de partie



* Création prioritaire d’ouvrières pour assurer la récolte.
* Création d’une éclaireuse afin de repérer rapidement les fleurs.



###### Milieu de partie



* Augmentation du nombre d’ouvrières jusqu’à un seuil de 10 ouvrière .
* Ajout d’une deuxième éclaireuse pour améliorer l’exploration.



###### Fin de partie



* Création de bourdons pour renforcer l’aspect offensif et la pression sur les adversaires avec un maximum de 3.
* Une réserve de nectar est toujours conservée pour éviter de se retrouver bloqué.



##### 3\. Comportement des abeilles

###### Ouvrières (OUV)



* Cherchent la fleur la plus rentable selon le ratio nectar / distance.
* Butinent lorsqu’elles sont à portée.
* Rentrent automatiquement à la ruche lorsqu’elles sont pleines.



###### Éclaireuses (ECL)



* Fonctionnement similaire aux ouvrières.



* Peuvent se déplacer en diagonale, ce qui leur permet d’explorer plus rapidement la carte.



###### Bourdons (BOU)



* N’ont pas de rôle de récolte.



* Se déplacent vers l’ennemi le plus proche.



* S’il n’y a pas d’ennemi visible, ils se dirigent vers le centre de la carte afin d’intercepter les adversaires.



##### 

##### 4 . Intelligence de Récolte et Mémoire Partagée



###### Mémoire du nectar :



L'IA mémorise la quantité de nectar présente sur chaque fleur visible à l'aide d'une

mémoire virtuelle partagée.



###### Anticipation de la récolte :



Lorsqu'une abeille décide d'aller butiner une fleur, la quantité de nectar qu'elle va récolter

est immédiatement déduite de la mémoire virtuelle. Les autres abeilles évitent ainsi de

cibler une fleur destinée à être vidée.



###### Score de rentabilité :



Pour chaque fleur visible, l'IA calcule un score de priorité selon la formule suivante :

Score = Quantité de Nectar / Distance



##### 5\. Déplacements et gestion des obstacles



* Une liste de cases interdites est maintenue à chaque tour pour éviter les collisions.
* Les déplacements sont calculés de manière progressive :

&nbsp;	- tentative de déplacement direct,

&nbsp;	- puis contournement si la case est bloquée.





##### 6\. Conclusion



Cette IA repose sur :



* une stratégie simple et progressive,
* une séparation claire des rôles entre les abeilles,
* un comportement adapté à chaque phase de la partie.











