# Documentation du Système de Pénalités Progressive

## Vue d'ensemble
Ce système permet de configurer des pénalités progressives pour les retards et sorties anticipées dans les Shift Types.

## Structure du Fichier JSON
**Fichier:** `custom_field_shift_late_early_assume_absent.json`

### 1. CHAMPS DE BASE (Shift Type)
```json
- late_entry_assume_as_absent: Seuil principal pour retard → absence
- early_exit_assume_as_absent: Seuil principal pour sortie anticipée → absence
```

### 2. CHAMPS INDICATEURS (Attendance)
```json
- late_entry_assume_as_absent: Checkbox pour marquer retard comme absence
- early_exit_assume_as_absent: Checkbox pour marquer sortie anticipée comme absence
```

### 3. SYSTÈME DE PÉNALITÉS PROGRESSIVE (4 Périodes)

#### PÉRIODE 1 - Seuil le plus bas
```json
- late_entry_assume_as_absent_1: Seuil retard période 1 (minutes)
- early_exit_assume_as_absent_1: Seuil sortie anticipée période 1 (minutes)  
- penalty_period_1: Pénalité appliquée période 1 (minutes)
```

#### PÉRIODE 2 - Seuil moyen
```json
- late_entry_assume_as_absent_2: Seuil retard période 2 (minutes)
- early_exit_assume_as_absent_2: Seuil sortie anticipée période 2 (minutes)
- penalty_period_2: Pénalité appliquée période 2 (minutes)
```

#### PÉRIODE 3 - Seuil élevé
```json
- late_entry_assume_as_absent_3: Seuil retard période 3 (minutes)
- early_exit_assume_as_absent_3: Seuil sortie anticipée période 3 (minutes)
- penalty_period_3: Pénalité appliquée période 3 (minutes)
```

#### PÉRIODE 4 - Seuil maximum
```json
- late_entry_assume_as_absent_4: Seuil retard période 4 (minutes)
- early_exit_assume_as_absent_4: Seuil sortie anticipée période 4 (minutes)
- penalty_period_4: Pénalité appliquée période 4 (minutes)
```

## Exemple de Configuration

### Scénario: Progressive Penalty System
```
Période 1: Retard 15 min → Absent + 30 min pénalité
Période 2: Retard 30 min → Absent + 60 min pénalité  
Période 3: Retard 45 min → Absent + 90 min pénalité
Période 4: Retard 60 min → Absent + 120 min pénalité
```

### Configuration dans Shift Type:
```
late_entry_assume_as_absent_1: 15
early_exit_assume_as_absent_1: 15  
penalty_period_1: 30

late_entry_assume_as_absent_2: 30
early_exit_assume_as_absent_2: 30
penalty_period_2: 60

late_entry_assume_as_absent_3: 45
early_exit_assume_as_absent_3: 45
penalty_period_3: 90

late_entry_assume_as_absent_4: 60
early_exit_assume_as_absent_4: 60
penalty_period_4: 120
```

## Logique d'Application

### Principe:
1. **Un seul champ de pénalité par période** - s'applique aux retards ET sorties anticipées
2. **Pénalité progressive** - plus le retard/sortie est important, plus la pénalité augmente
3. **Absence automatique** - dépassement du seuil → marqué absent + pénalité

### Algorithme:
```python
if retard >= late_entry_assume_as_absent_4:
    # Absence + penalty_period_4
elif retard >= late_entry_assume_as_absent_3:
    # Absence + penalty_period_3  
elif retard >= late_entry_assume_as_absent_2:
    # Absence + penalty_period_2
elif retard >= late_entry_assume_as_absent_1:
    # Absence + penalty_period_1
```

## Ordre des Champs dans l'Interface
Les champs apparaîtront dans cet ordre dans Shift Type:
1. late_entry_assume_as_absent (champ de base)
2. early_exit_assume_as_absent (champ de base)
3. **Période 1:** late_entry_1 → early_exit_1 → penalty_1
4. **Période 2:** late_entry_2 → early_exit_2 → penalty_2  
5. **Période 3:** late_entry_3 → early_exit_3 → penalty_3
6. **Période 4:** late_entry_4 → early_exit_4 → penalty_4

## Application
```bash
bench --site votre-site migrate
```

Cette commande appliquera tous les nouveaux champs dans la base de données.
