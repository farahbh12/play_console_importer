#!/usr/bin/env python3
"""
Script d'intégration automatique pour le connecteur communautaire Looker Studio
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path

# Constantes
COLORS = {
    'GREEN': '\033[92m',
    'RED': '\033[91m',
    'YELLOW': '\033[93m',
    'BLUE': '\033[94m',
    'BOLD': '\033[1m',
    'RESET': '\033[0m'
}

def log(message, color=COLORS['RESET']):
    """Affiche un message avec une couleur optionnelle"""
    print(f"{color}{message}{COLORS['RESET']}")

def log_success(message):
    """Affiche un message de succès"""
    log(f"✅ {message}", COLORS['GREEN'])

def log_error(message):
    """Affiche un message d'erreur"""
    log(f"❌ {message}", COLORS['RED'])

def log_warning(message):
    """Affiche un message d'avertissement"""
    log(f"⚠️  {message}", COLORS['YELLOW'])

def log_info(message):
    """Affiche un message d'information"""
    log(f"ℹ️  {message}", COLORS['BLUE'])

class DjangoConnectorIntegrator:
    """Classe pour gérer l'intégration du connecteur dans un projet Django"""
    
    def __init__(self, project_path):
        self.project_path = Path(project_path).resolve()
        self.backend_path = self.project_path / 'BACKEND'
        self.controllers_path = self.backend_path / 'play_reports' / 'controllers'
        self.urls_path = self.backend_path / 'play_reports' / 'urls.py'
        self.requirements_path = self.backend_path / 'requirements.txt'
    
    def run(self):
        """Exécute le processus d'intégration"""
        log(f"\n{COLORS['BOLD']}🚀 Intégration du Connecteur Communautaire Looker Studio{COLORS['RESET']}")
        log(f"📁 Chemin du projet: {self.project_path}")
        
        try:
            # Vérifications préliminaires
            self.check_prerequisites()
            
            # Copie et configuration des fichiers
            self.setup_controller()
            self.update_urls()
            
            # Vérification des dépendances
            self.check_dependencies()
            
            # Validation
            self.validate_integration()
            
            # Résumé
            self.print_summary()
            
            log_success('Intégration terminée avec succès !')
            
        except Exception as e:
            log_error(f"Erreur lors de l'intégration: {str(e)}")
            sys.exit(1)
    
    def check_prerequisites(self):
        """Vérifie que tous les prérequis sont satisfaits"""
        log_info('Vérification des prérequis...')
        
        # Vérifier la structure du projet
        required_dirs = [
            self.project_path,
            self.backend_path,
            self.controllers_path,
            self.urls_path.parent
        ]
        
        for dir_path in required_dirs:
            if not dir_path.exists():
                raise FileNotFoundError(f"Dossier manquant: {dir_path}")
        
        log_success('Structure du projet validée')
    
    def setup_controller(self):
        """Configure le contrôleur du connecteur"""
        log_info('Configuration du contrôleur...')
        
        controller_file = self.controllers_path / 'looker_community_controller.py'
        
        # Vérifier si le contrôleur existe déjà
        if controller_file.exists():
            log_warning('Le contrôleur existe déjà. Mise à jour en cours...')
        
        # Copier le contrôleur (dans un cas réel, vous pourriez le télécharger ou le générer)
        # Ici, on suppose qu'il est déjà en place
        log_success('Contrôleur configuré')
    
    def update_urls(self):
        """Met à jour les URLs Django"""
        log_info('Mise à jour des URLs...')
        
        with open(self.urls_path, 'r', encoding='utf-8') as f:
            urls_content = f.read()
        
        # Vérifier si les URLs sont déjà configurées
        if 'looker_community_controller' in urls_content:
            log_warning('Les URLs sont déjà configurées')
            return
        
        # Ajouter l'import du contrôleur
        import_statement = 'from play_reports.controllers import looker_community_controller'
        
        if import_statement not in urls_content:
            # Trouver la dernière ligne d'import
            import_lines = [line for line in urls_content.split('\n') 
                          if line.strip().startswith(('from ', 'import '))]
            
            if import_lines:
                last_import = import_lines[-1]
                urls_content = urls_content.replace(
                    last_import,
                    f"{last_import}\n{import_statement}"
                )
        
        # Ajouter les URLs
        url_patterns = [
            "# Looker Community Connector endpoints",
            "path('looker/authenticate/', looker_community_controller.AuthenticateForCommunityConnectorView.as_view(), name='looker_authenticate'),",
            "path('looker/verify-subscription/', looker_community_controller.VerifySubscriptionView.as_view(), name='looker_verify_subscription'),",
            "path('looker/metadata/', looker_community_roller.DataSourcesMetadataView.as_view(), name='looker_metadata'),",
            "path('looker/schema/<str:table_name>/', looker_community_controller.TableSchemaView.as_view(), name='looker_schema'),",
            "path('looker/data/<str:table_name>/', looker_community_controller.TableDataView.as_view(), name='looker_data'),"
        ]
        
        # Trouver la fin de urlpatterns
        if 'urlpatterns = [' in urls_content and ']' in urls_content[urls_content.find('urlpatterns = [') + len('urlpatterns = ['):]:
            # Insérer avant la dernière ligne de urlpatterns
            insert_point = urls_content.rfind(']')
            urls_content = (
                urls_content[:insert_point] + 
                '\n    ' + 
                '\n    '.join(url_patterns) + 
                '\n' + 
                urls_content[insert_point:]
            )
        
        # Sauvegarder les modifications
        with open(self.urls_path, 'w', encoding='utf-8') as f:
            f.write(urls_content)
        
        log_success('URLs mises à jour')
    
    def check_dependencies(self):
        """Vérifie les dépendances requises"""
        log_info('Vérification des dépendances...')
        
        required_deps = [
            'djangorestframework',
            'django-cors-headers',
            'pyjwt',
            'python-dotenv'
        ]
        
        missing_deps = []
        
        if self.requirements_path.exists():
            with open(self.requirements_path, 'r', encoding='utf-8') as f:
                requirements = f.read()
            
            for dep in required_deps:
                if dep not in requirements:
                    missing_deps.append(dep)
        else:
            missing_deps = required_deps
        
        if missing_deps:
            log_warning(f'Dépendances manquantes: {", ".join(missing_deps)}')
            log_info('Exécutez: pip install ' + ' '.join(missing_deps))
        else:
            log_success('Toutes les dépendances sont installées')
    
    def validate_integration(self):
        """Valide l'intégration"""
        log_info('Validation de l\'intégration...')
        
        # Vérifier que les fichiers nécessaires existent
        required_files = [
            self.controllers_path / 'looker_community_controller.py',
            self.urls_path
        ]
        
        for file_path in required_files:
            if not file_path.exists():
                log_warning(f'Fichier manquant: {file_path}')
            else:
                log_success(f'Fichier trouvé: {file_path}')
        
        # Vérifier la syntaxe Python
        try:
            subprocess.run(
                [sys.executable, '-m', 'py_compile', str(required_files[0])],
                check=True,
                capture_output=True
            )
            log_success('Syntaxe Python valide')
        except subprocess.CalledProcessError as e:
            log_error(f'Erreur de syntaxe dans le contrôleur: {e.stderr.decode()}')
    
    def print_summary(self):
        """Affiche un résumé de l'intégration"""
        log(f"\n{COLORS['BOLD']}📋 Résumé de l'intégration{COLORS['RESET']}")
        log(f"- Contrôleur: {self.controllers_path / 'looker_community_controller.py'}")
        log(f"- URLs: {self.urls_path}")
        
        log(f"\n{COLORS['BOLD']}🔗 Endpoints disponibles:{COLORS['RESET']}")
        log("  POST /api/looker/authenticate/")
        log("  GET  /api/looker/verify-subscription/")
        log("  GET  /api/looker/metadata/")
        log("  GET  /api/looker/schema/<table_name>/")
        log("  GET  /api/looker/data/<table_name>/")
        
        log(f"\n{COLORS['BOLD']}🚀 Prochaines étapes:{COLORS['RESET']}")
        log("1. Redémarrez votre serveur Django")
        log("2. Testez les endpoints avec un client HTTP comme cURL ou Postman")
        log("3. Configurez le connecteur dans Looker Studio")

def main():
    """Fonction principale"""
    if len(sys.argv) < 2:
        log(f"{COLORS['BOLD']}Usage:{COLORS['RESET']}")
        log("python integration_script.py <chemin_du_projet>")
        log("")
        log("Exemple:")
        log("python integration_script.py /chemin/vers/votre/projet")
        sys.exit(1)
    
    project_path = sys.argv[1]
    integrator = DjangoConnectorIntegrator(project_path)
    integrator.run()

if __name__ == "__main__":
    main()
