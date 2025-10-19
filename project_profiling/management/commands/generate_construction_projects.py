# management/commands/generate_construction_projects.py

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
import random
from datetime import date, timedelta
from faker import Faker
from django.contrib.auth import get_user_model
from django.urls import reverse

# Import your models (adjust app names as needed)
from authentication.models import UserProfile
from project_profiling.models import ProjectType, ProjectProfile, ProjectBudget, FundAllocation, CostCategory
from scheduling.models import ProjectScope, ProjectTask
from manage_client.models import Client
from notifications.models import Notification, NotificationStatus

User = get_user_model()
fake = Faker(['en_PH'])

class Command(BaseCommand):
    help = 'Generate realistic construction project data'

    def add_arguments(self, parser):
        parser.add_argument('--projects', type=int, default=10)
        parser.add_argument('--with-tasks', action='store_true')
        parser.add_argument('--with-budgets', action='store_true')
        parser.add_argument('--with-notifications', action='store_true')
        parser.add_argument('--clear-existing', action='store_true')

    def handle(self, *args, **options):
        if options['clear_existing']:
            self.stdout.write(self.style.WARNING('Clearing existing data...'))
            self.clear_existing_data()

        num_projects = options['projects']
        self.stdout.write(f'Generating {num_projects} construction projects...')

        self.create_project_types()
        self.create_users()
        self.create_clients()

        projects = self.create_projects(num_projects)

        if options['with_tasks']:
            self.create_project_scopes_and_tasks(projects)
        if options['with_budgets']:
            self.create_budgets_and_allocations(projects)
        if options['with_notifications']:
            self.create_notifications()

        self.stdout.write(self.style.SUCCESS(f'Successfully generated {num_projects} construction projects!'))

    # ------------------- Data Clearing -------------------
    def clear_existing_data(self):
        ProjectProfile.objects.all().delete()
        ProjectType.objects.all().delete()
        Client.objects.all().delete()

    # ------------------- Project Types -------------------
    def create_project_types(self):
        project_types = [
            {"name": "Residential Building", "code": "RES", "description": "Single/multi-family homes, condos, apartments"},
            {"name": "Commercial Building", "code": "COM", "description": "Office buildings, retail stores, restaurants"},
            {"name": "Industrial Facility", "code": "IND", "description": "Factories, warehouses, manufacturing plants"},
            {"name": "Infrastructure", "code": "INF", "description": "Roads, bridges, utilities, public works"},
            {"name": "Renovation", "code": "REN", "description": "Building renovations and improvements"},
            {"name": "Mixed-Use Development", "code": "MIX", "description": "Combined residential and commercial"},
        ]
        for pt_data in project_types:
            ProjectType.objects.get_or_create(code=pt_data["code"], defaults=pt_data)

    # ------------------- Users -------------------
    def create_users(self):
        roles_data = [
            ("Operations Manager", "OM", 2),
            ("Project Manager", "PM", 5),
            ("Engineer", "EG", 8),
            ("View Only", "VO", 3),
        ]
        for role_name, role_code, count in roles_data:
            for i in range(count):
                first_name = fake.first_name()
                last_name = fake.last_name()
                email = f"{role_code.lower()}_user_{i+1}@constructionco.ph"
                user, created = User.objects.get_or_create(email=email, defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'is_active': True,
                })
                if created:
                    user.set_password('password123')
                    user.save()
                UserProfile.objects.get_or_create(user=user, defaults={'role': role_code})

    # ------------------- Clients -------------------
    def create_clients(self):
        clients_data = [
            {"company_name": "Ayala Land Inc.", "contact_name": "Maria Santos", "client_type": "DC"},
            {"company_name": "DMCI Holdings", "contact_name": "Roberto Cruz", "client_type": "DC"},
            {"company_name": "SM Development Corporation", "contact_name": "Carmen Lopez", "client_type": "DC"},
            {"company_name": "Megaworld Corporation", "contact_name": "Juan Reyes", "client_type": "DC"},
            {"company_name": "D.M. Consunji Inc.", "contact_name": "Antonio Mendoza", "client_type": "GC"},
            {"company_name": "EEI Corporation", "contact_name": "Sofia Villanueva", "client_type": "GC"},
            {"company_name": "Megawide Construction", "contact_name": "Diego Torres", "client_type": "GC"},
            {"company_name": "Department of Public Works", "contact_name": "Isabella Garcia", "client_type": "DC"},
            {"company_name": "Local Government Unit - Manila", "contact_name": "Miguel Fernandez", "client_type": "DC"},
            {"company_name": "Private Homeowner", "contact_name": "Ana Rodriguez", "client_type": "DC"},
        ]
        created_by = UserProfile.objects.filter(role="OM").first()
        for client_data in clients_data:
            client_data.update({
                'email': fake.email(),
                'phone': f"+63{fake.random_int(min=900000000, max=999999999)}",
                'address': fake.address(),
                'city': fake.city(),
                'state': random.choice(['Metro Manila', 'Cebu', 'Davao', 'Iloilo', 'Baguio']),
                'zip_code': fake.postcode(),
                'created_by': created_by,
            })
            Client.objects.get_or_create(company_name=client_data["company_name"], defaults=client_data)

    # ------------------- Projects -------------------
    def create_projects(self, count):
        projects = []
        project_types = list(ProjectType.objects.all())
        clients = list(Client.objects.all())
        pms = list(UserProfile.objects.filter(role="PM"))
        engineers = list(UserProfile.objects.filter(role="EG"))
        creators = list(UserProfile.objects.filter(role__in=["OM", "PM"]))

        # --- Locations and Coordinates ---
        locations = [
            "Makati City, Metro Manila",
            "Bonifacio Global City, Taguig",
            "Ortigas Center, Pasig City",
            "Cebu IT Park, Cebu City",
            "Alabang, Muntinlupa City",
            "Eastwood City, Quezon City",
            "Clark Freeport Zone, Pampanga",
            "Iloilo Business Park, Iloilo City",
            "Davao City, Davao del Sur",
            "Baguio City, Benguet"
        ]
        location_coords = {
            "Makati City, Metro Manila": (14.5547, 121.0244),
            "Bonifacio Global City, Taguig": (14.5446, 121.0567),
            "Ortigas Center, Pasig City": (14.5869, 121.0614),
            "Cebu IT Park, Cebu City": (10.3280, 123.9040),
            "Alabang, Muntinlupa City": (14.4170, 121.0424),
            "Eastwood City, Quezon City": (14.6091, 121.0791),
            "Clark Freeport Zone, Pampanga": (15.1840, 120.5498),
            "Iloilo Business Park, Iloilo City": (10.7108, 122.5477),
            "Davao City, Davao del Sur": (7.1907, 125.4553),
            "Baguio City, Benguet": (16.4023, 120.5960),
        }

        project_name_templates = [
            "The {} Tower",
            "{} Corporate Center",
            "{} Residences",
            "{} Business Park",
            "{} Commercial Complex",
            "Metro {} Development",
            "{} Infrastructure Project",
            "{} Renovation Phase {}",
        ]

        for i in range(count):
            project_type = random.choice(project_types)
            client = random.choice(clients)
            location = random.choice(locations)

            # Generate GPS coordinates with small random variation
            base_lat, base_lng = location_coords.get(location, (14.5995, 120.9842))  # default: Manila
            latitude = round(base_lat + random.uniform(-0.02, 0.02), 6)
            longitude = round(base_lng + random.uniform(-0.02, 0.02), 6)
            gps_coordinates = f"{latitude}, {longitude}"

            # --- Project Name ---
            location_name = location.split(',')[0].replace(' City', '').replace(' Center', '')
            template = random.choice(project_name_templates)
            if 'Phase {}' in template:
                project_name = template.format(location_name, random.randint(1, 3))
            else:
                project_name = template.format(location_name)

            # --- Dates ---
            start_date = fake.date_between(start_date='-2y', end_date='+6m')
            duration_days = random.randint(30, 730)
            target_completion = start_date + timedelta(days=duration_days)

            # --- Budget ---
            budget_ranges = {
                'RES': (500000, 15000000),
                'COM': (2000000, 50000000),
                'IND': (5000000, 200000000),
                'INF': (10000000, 500000000),
                'REN': (200000, 5000000),
                'MIX': (3000000, 100000000),
            }
            min_budget, max_budget = budget_ranges.get(project_type.code, (500000, 10000000))
            estimated_cost = random.randint(min_budget, max_budget)
            approved_budget = estimated_cost * random.uniform(0.95, 1.15)

            # --- Status & Progress ---
            status_weights = [("PL", 15), ("OG", 60), ("CP", 20), ("CN", 5)]
            status = random.choices([s[0] for s in status_weights], weights=[s[1] for s in status_weights])[0]

            if status == "CP":
                progress = 100
                actual_completion_date = target_completion + timedelta(days=random.randint(-30, 90))
            elif status == "OG":
                progress = random.randint(5, 95)
                actual_completion_date = None
            else:
                progress = random.randint(0, 10) if status == "PL" else 0
                actual_completion_date = None

            project_data = {
                'created_by': random.choice(creators),
                'assigned_to': random.choice(pms) if random.choice([True, False]) else None,
                'project_manager': random.choice(pms),
                'client': client,
                'project_source': client.client_type,
                'project_name': project_name,
                'project_type': project_type,
                'project_category': random.choice(['PUB', 'PRI', 'REN', 'NEW']),
                'description': fake.text(max_nb_chars=500),
                'location': location,
                'city_province': location.split(',')[-1].strip(),
                'gps_coordinates': gps_coordinates,
                'start_date': start_date,
                'target_completion_date': target_completion,
                'actual_completion_date': actual_completion_date,
                'estimated_cost': Decimal(str(estimated_cost)),
                'approved_budget': Decimal(str(round(approved_budget))),
                'site_engineer': random.choice(engineers).full_name,
                'subcontractors': ', '.join([fake.company() for _ in range(random.randint(1, 4))]),
                'status': status,
                'progress': Decimal(str(progress)),
                'payment_terms': random.choice([
                    "30% down, 70% upon completion",
                    "Progressive billing monthly",
                    "25% down, 25% at 50% completion, 50% upon completion",
                    "Net 30 days"
                ])
            }

            project = ProjectProfile.objects.create(**project_data)
            projects.append(project)
            self.stdout.write(f'  Created project: {project.project_name} ({project.project_id})')

        return projects


    def create_project_scopes_and_tasks(self, projects):
        """Create realistic project scopes and tasks"""
        
        # Common construction scopes with typical weights
        scope_templates = {
            'RES': [
                ("Site Preparation", 5),
                ("Foundation Work", 15),
                ("Structural Framework", 25),
                ("Roofing", 10),
                ("Electrical Installation", 12),
                ("Plumbing Installation", 10),
                ("Interior Finishing", 18),
                ("Final Inspection", 5)
            ],
            'COM': [
                ("Site Preparation", 3),
                ("Foundation & Excavation", 12),
                ("Structural Steel/Concrete", 30),
                ("MEP Installation", 20),
                ("Façade & Envelope", 15),
                ("Interior Build-out", 15),
                ("Final Commissioning", 5)
            ],
            'IND': [
                ("Site Development", 5),
                ("Foundation Systems", 15),
                ("Structural Framework", 25),
                ("Process Equipment", 20),
                ("Utilities & MEP", 20),
                ("Safety Systems", 10),
                ("Startup & Testing", 5)
            ],
            'INF': [
                ("Planning & Design", 8),
                ("Site Clearing", 7),
                ("Earthwork & Excavation", 20),
                ("Concrete Structures", 25),
                ("Utilities Installation", 15),
                ("Paving & Surfacing", 15),
                ("Final Inspection", 10)
            ]
        }

        # Task templates for each scope type
        task_templates = {
            "Site Preparation": [
                ("Survey & Layout", 20),
                ("Clearing & Grubbing", 30),
                ("Temporary Facilities", 25),
                ("Access Roads", 25)
            ],
            "Foundation Work": [
                ("Excavation", 25),
                ("Footings Installation", 35),
                ("Foundation Walls", 40)
            ],
            "Structural Framework": [
                ("Column Installation", 30),
                ("Beam Placement", 25),
                ("Floor Slab Pouring", 25),
                ("Structural Inspection", 20)
            ],
            "MEP Installation": [
                ("Electrical Rough-in", 30),
                ("Plumbing Rough-in", 30),
                ("HVAC Installation", 25),
                ("Fire Safety Systems", 15)
            ],
            "Interior Finishing": [
                ("Drywall Installation", 25),
                ("Flooring Installation", 30),
                ("Painting", 20),
                ("Fixture Installation", 25)
            ]
        }

        pm_users = list(UserProfile.objects.filter(role="PM"))

        for project in projects:
            project_code = project.project_type.code if project.project_type else 'RES'
            scopes_data = scope_templates.get(project_code, scope_templates['RES'])
            
            # Create scopes
            for scope_name, weight in scopes_data:
                scope = ProjectScope.objects.create(
                    project=project,
                    name=scope_name,
                    weight=Decimal(str(weight))
                )
                
                # Create tasks for this scope
                tasks_data = task_templates.get(scope_name, [
                    (f"{scope_name} Task 1", 50),
                    (f"{scope_name} Task 2", 50)
                ])
                
                project_duration = (project.target_completion_date - project.start_date).days
                scope_duration = int(project_duration * (weight / 100))
                task_start = project.start_date
                
                for task_name, task_weight in tasks_data:
                    task_duration = max(1, int(scope_duration * (task_weight / 100)))
                    task_end = task_start + timedelta(days=task_duration - 1)
                    
                    # Calculate task progress based on project progress
                    if project.status == "CP":
                        task_progress = 100
                    elif project.status == "OG":
                        # Vary task progress realistically
                        base_progress = float(project.progress)
                        task_progress = max(0, min(100, 
                            base_progress + random.uniform(-20, 20)
                        ))
                    else:
                        task_progress = 0

                    ProjectTask.objects.create(
                        project=project,
                        task_name=task_name,
                        description=f"Complete {task_name.lower()} for {scope_name.lower()}",
                        scope=scope,
                        assigned_to=random.choice(pm_users),
                        start_date=task_start,
                        end_date=task_end,
                        weight=Decimal(str(task_weight)),
                        progress=Decimal(str(task_progress))
                    )
                    
                    task_start = task_end + timedelta(days=1)
            
            self.stdout.write(f'  Created scopes and tasks for: {project.project_name}')

    def create_budgets_and_allocations(self, projects):
        """Create realistic budgets and fund allocations"""
        
        for project in projects:
            if not project.approved_budget:
                continue
                
            scopes = project.scopes.all()
            if not scopes:
                continue
                
            total_budget = float(project.approved_budget)
            
            for scope in scopes:
                scope_budget = total_budget * (float(scope.weight) / 100)
                
                # Distribute scope budget across cost categories
                categories = [
                    (CostCategory.LABOR, 0.4),       # 40%
                    (CostCategory.MATERIALS, 0.35),   # 35%
                    (CostCategory.EQUIPMENT, 0.15),   # 15%
                    (CostCategory.SUBCONTRACTOR, 0.08), # 8%
                    (CostCategory.OTHER, 0.02),       # 2%
                ]
                
                for category, percentage in categories:
                    if random.choice([True, True, True, False]):  # 75% chance to include
                        category_amount = scope_budget * percentage * random.uniform(0.8, 1.2)
                        
                        budget = ProjectBudget.objects.create(
                            project=project,
                            scope=scope,
                            category=category,
                            planned_amount=Decimal(str(round(category_amount, 2)))
                        )
                        
                        # Create some fund allocations
                        if random.choice([True, False, False]):  # 33% chance
                            allocation_count = random.randint(1, 3)
                            remaining_amount = float(budget.planned_amount)
                            
                            for i in range(allocation_count):
                                allocation_amount = remaining_amount * random.uniform(0.2, 0.8)
                                remaining_amount -= allocation_amount
                                
                                FundAllocation.objects.create(
                                    project_budget=budget,
                                    amount=Decimal(str(round(allocation_amount, 2))),
                                    date_allocated=fake.date_between(
                                        start_date=project.start_date,
                                        end_date=min(project.target_completion_date, date.today())
                                    ),
                                    note=f"Allocation #{i+1} for {budget.get_category_display()}"
                                )
                                
                                if remaining_amount <= 0:
                                    break
            
            self.stdout.write(f'  Created budgets for: {project.project_name}')

    def create_notifications(self):
        oms = UserProfile.objects.filter(role="OM")
        pms = UserProfile.objects.filter(role="PM")
        egs = UserProfile.objects.filter(role="EG")

        # --- Simulate new project submissions ---
        for project in ProjectProfile.objects.all()[:5]:
            # Notify EGs
            for eg in egs:
                notif = Notification.objects.create(
                    message=(
                        f"{project.created_by.full_name if hasattr(project, 'created_by') else 'System'} "
                        f"submitted a new project '{project.project_name}' for approval."
                    ),
                    link=reverse("review_staging_project_list"),
                )
                NotificationStatus.objects.create(notification=notif, user=eg)

            # Notify the OM themselves
            if oms.exists():
                om = random.choice(oms)
                notif_self = Notification.objects.create(
                    message=(
                        f"You submitted the project '{project.project_name}'. "
                        f"Waiting for approval from Engineers."
                    ),
                    link=reverse(
                        "project_list_direct_client"
                        if getattr(project, "project_type", None) == "DC"
                        else "project_list_general_contractor",
                        kwargs={"token": "demo-token", "role": om.role},
                    ),
                )
                NotificationStatus.objects.create(notification=notif_self, user=om)

                self.stdout.write(f"  ✅ OM notified for {project.project_name}")

        # --- Simulate progress report submissions ---
        for task in ProjectTask.objects.all()[:10]:
            # Notify OMs and EGs
            om_eg_users = UserProfile.objects.filter(role__in=["OM", "EG"])
            notif_message = (
                f"{task.assigned_to.full_name if hasattr(task, 'assigned_to') else 'System'} "
                f"submitted a progress report for Project '{task.project.project_name}' "
                f"(Task: {task.task_name})"
            )

            if om_eg_users.exists():
                notif = Notification.objects.create(
                    message=notif_message,
                    link=reverse("review_updates"),
                )
                for user in om_eg_users:
                    NotificationStatus.objects.create(notification=notif, user=user)

                # Notify the PM themselves
                if pms.exists():
                    pm = random.choice(pms)
                    notif_pm = Notification.objects.create(
                        message=(
                            f"You submitted a progress report for Project "
                            f"'{task.project.project_name}' (Task: {task.task_name})"
                        ),
                        link=reverse(
                            "task_list",
                            kwargs={
                                "project_id": task.project.id,
                                "token": "demo-token",
                                "role": pm.role,
                            },
                        ),
                    )
                    NotificationStatus.objects.create(notification=notif_pm, user=pm)

                    self.stdout.write(
                        f"  📊 PM notified for {task.project.project_name} - {task.task_name}"
                    )
