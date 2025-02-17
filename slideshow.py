import gurobipy as gp
from gurobipy import GRB
import sys
import logging
import argparse

def read_input(file_path):
    """Lit les donnees du fichier d'entree et retourne les informations sous forme exploitable."""
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    num_photos = int(lines[0].strip())
    horizontal = []
    vertical = []
    
    for i in range(1, num_photos + 1):
        parts = lines[i].strip().split()
        orientation = parts[0]
        tags = set(parts[2:])
        if orientation == 'H':
            horizontal.append((i - 1, tags))
        else:
            vertical.append((i - 1, tags))
    
    # Associer les photos verticales par paires sequentiellement
    vertical_pairs = []
    vertical.sort(key=lambda x: len(x[1]))  # Trier pour potentiellement ameliorer l'association
    for i in range(0, len(vertical) - 1, 2):
        vertical_pairs.append((vertical[i][0], vertical[i+1][0], vertical[i][1] | vertical[i+1][1]))
    
    slides = horizontal + vertical_pairs
    
    return slides

def interest_factor(tags1, tags2):
    """Calcule le score de transition entre deux slides."""
    if not isinstance(tags1, set) or not isinstance(tags2, set):
        return 0
    return min(len(tags1 & tags2), len(tags1 - tags2), len(tags2 - tags1))

def optimize_slideshow(slides):
    """Construit et resout le modele d'optimisation avec Gurobi."""
    model = gp.Model("hashcode2019")
    
    num_slides = len(slides)
    
    # Variables binaires : x[i, j] = 1 si la diapositive i est suivie de la diapositive j
    x = model.addVars(num_slides, num_slides, vtype=GRB.BINARY, name="x")
    
    # Objectif : maximiser la somme des interets entre diapositives adjacentes
    model.setObjective(gp.quicksum(interest_factor(slides[i][1], slides[j][1]) * x[i, j]
                                   for i in range(num_slides) for j in range(num_slides) if i != j),
                       GRB.MAXIMIZE)
    
    # Contraintes : chaque diapositive doit apparaitre au plus une fois
    for i in range(num_slides):
        model.addConstr(gp.quicksum(x[i, j] for j in range(num_slides) if i != j) <= 1, name=f"slide_out_{i}")
        model.addConstr(gp.quicksum(x[j, i] for j in range(num_slides) if i != j) <= 1, name=f"slide_in_{i}")
    
    model.optimize()
    
    solution = []
    for i in range(num_slides):
        for j in range(num_slides):
            if i != j and x[i, j].x > 0.5:
                slide_id = slides[i][0] if isinstance(slides[i][0], int) else f"{slides[i][0]} {slides[i][1]}"
                solution.append(slide_id)
    
    return solution

def write_output(solution, output_path):
    """Ecrit la solution dans un fichier output."""
    with open(output_path, 'w') as f:
        f.write(str(len(solution)) + '\n')
        for slide in solution:
            f.write(str(slide) + '\n')

if __name__ == "__main__":
    # Configuration de l'argument parser pour accepter un fichier d'entree via la ligne de commande
    parser = argparse.ArgumentParser(description="Optimisation du diaporama avec Gurobi pour HashCode 2019")
    parser.add_argument('input_file', type=str, help="Le fichier d'entree contenant les donnees des photos")
    parser.add_argument('--output_file', type=str, default="slideshow.sol", help="Le fichier de sortie (par defaut : slideshow.sol)")
    
    args = parser.parse_args()
    
    input_file = args.input_file
    output_file = args.output_file
    
    # Verification si le fichier d'entree existe
    try:
        logging.info(f"Lecture du fichier d'entree : {input_file}")
        slides = read_input(input_file)
        logging.info(f"Nombre de diapositives generees : {len(slides)}")
        
        logging.info("Optimisation en cours...")
        solution = optimize_slideshow(slides)
        
        logging.info(f"Ecriture du fichier de sortie : {output_file}")
        write_output(solution, output_file)
        logging.info("Processus termine avec succes.")
    
    except FileNotFoundError:
        logging.error(f"Le fichier {input_file} n'a pas ete trouve. Veuillez verifier le chemin.")
    except Exception as e:
        logging.error(f"Une erreur s'est produite : {e}")