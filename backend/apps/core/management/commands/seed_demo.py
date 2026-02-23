from datetime import timedelta
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.communities.models import Community, Membership
from apps.profiles.models import Profile
from apps.requests.models import Request, VolunteerOffer
from apps.chat.models import Conversation, Message
from apps.reports.models import Report
from apps.loans.models import LoanItem, LoanRequest

User = get_user_model()


class Command(BaseCommand):
    help = 'Carga datos de demo para el MVP con dos comunidades.'

    def handle(self, *args, **options):
        now = timezone.now()

        obanos, _ = Community.objects.get_or_create(
            name='Obanos',
            defaults={'description': 'Comunidad local de Obanos para el MVP.'},
        )
        com_vecinos, _ = Community.objects.get_or_create(
            name='Com. Vecinos',
            defaults={'description': 'Comunidad de vecinos para pruebas del MVP.'},
        )
        communities_by_name = {
            'Obanos': obanos,
            'Com. Vecinos': com_vecinos,
        }

        # Elimina comunidades no objetivo para evitar restos de seeds antiguos
        extra_communities = Community.objects.exclude(id__in=[obanos.id, com_vecinos.id])
        for extra_community in extra_communities:
            LoanRequest.objects.filter(item__community=extra_community).delete()
            LoanItem.objects.filter(community=extra_community).delete()
            Message.objects.filter(conversation__request__community=extra_community).delete()
            Conversation.objects.filter(request__community=extra_community).delete()
            VolunteerOffer.objects.filter(request__community=extra_community).delete()
            Report.objects.filter(request__community=extra_community).delete()
            Request.objects.filter(community=extra_community).delete()
            Membership.objects.filter(community=extra_community).delete()
            extra_community.delete()

        # Limpia datos previos en ambas comunidades demo
        for community in communities_by_name.values():
            LoanRequest.objects.filter(item__community=community).delete()
            LoanItem.objects.filter(community=community).delete()
            Message.objects.filter(conversation__request__community=community).delete()
            Conversation.objects.filter(request__community=community).delete()
            VolunteerOffer.objects.filter(request__community=community).delete()
            Report.objects.filter(request__community=community).delete()
            Request.objects.filter(community=community).delete()

        demo_users = [
            ('maria.garcia@example.com', 'María García'),
            ('juan.lopez@example.com', 'Juan López'),
            ('ana.martinez@example.com', 'Ana Martínez'),
            ('pedro.sanchez@example.com', 'Pedro Sánchez'),
            ('carmen.ruiz@example.com', 'Carmen Ruiz'),
            ('luis.moreno@example.com', 'Luis Moreno'),
            ('laura.gomez@example.com', 'Laura Gómez'),
            ('carlos.navarro@example.com', 'Carlos Navarro'),
            ('nuria.fernandez@example.com', 'Nuria Fernández'),
            ('diego.perez@example.com', 'Diego Pérez'),
            ('ines.rodriguez@example.com', 'Inés Rodríguez'),
            ('miguel.santos@example.com', 'Miguel Santos'),
        ]

        users = {}
        for email, display_name in demo_users:
            user, created = User.objects.get_or_create(username=email, defaults={'email': email})
            if created:
                user.set_password('Demo1234!')
                user.save()
            Profile.objects.update_or_create(user=user, defaults={'display_name': display_name})
            users[display_name] = user

        # Limpieza de memberships legacy para evitar comunidades fantasma en demo users
        demo_user_ids = [u.id for u in users.values()]
        Membership.objects.filter(user_id__in=demo_user_ids).exclude(
            community_id__in=[obanos.id, com_vecinos.id]
        ).delete()

        # Memberships: todos en Obanos, y un subconjunto en Com. Vecinos
        for display_name, user in users.items():
            role_obanos = Membership.Role.MODERATOR if display_name == 'Carlos Navarro' else Membership.Role.MEMBER
            Membership.objects.update_or_create(
                user=user,
                community=obanos,
                defaults={
                    'status': Membership.Status.APPROVED,
                    'role_in_community': role_obanos,
                    'joined_at': now - timedelta(days=800),
                },
            )

        com_vecinos_members = {
            'Ana Martínez': Membership.Role.MEMBER,
            'Carmen Ruiz': Membership.Role.MEMBER,
            'Luis Moreno': Membership.Role.MEMBER,
            'Laura Gómez': Membership.Role.MODERATOR,
            'Nuria Fernández': Membership.Role.MEMBER,
            'Diego Pérez': Membership.Role.MEMBER,
            'Miguel Santos': Membership.Role.MEMBER,
        }
        com_vecinos_member_ids = [users[name].id for name in com_vecinos_members.keys()]
        Membership.objects.filter(
            user_id__in=demo_user_ids,
            community=com_vecinos,
        ).exclude(user_id__in=com_vecinos_member_ids).delete()

        for display_name, role in com_vecinos_members.items():
            Membership.objects.update_or_create(
                user=users[display_name],
                community=com_vecinos,
                defaults={
                    'status': Membership.Status.APPROVED,
                    'role_in_community': role,
                    'joined_at': now - timedelta(days=600),
                },
            )

        # Superadmin demo global
        admin_user, _ = User.objects.get_or_create(
            username='admin@example.com',
            defaults={
                'email': 'admin@example.com',
                'is_staff': True,
                'is_superuser': True,
            },
        )
        admin_user.set_password('AdminDemo1234!')
        if not admin_user.is_staff or not admin_user.is_superuser:
            admin_user.is_staff = True
            admin_user.is_superuser = True
        admin_user.email = 'admin@example.com'
        admin_user.save()
        Profile.objects.update_or_create(
            user=admin_user,
            defaults={'display_name': 'Superadmin Demo'},
        )

        def set_dates(instance, created_at, updated_at=None, closed_at=None):
            if updated_at is None:
                updated_at = created_at
            instance.__class__.objects.filter(id=instance.id).update(
                created_at=created_at,
                updated_at=updated_at,
                closed_at=closed_at,
            )

        def create_request(data):
            creator = users[data['creator']]
            community = communities_by_name[data.get('community', 'Obanos')]
            req = Request.objects.create(
                community=community,
                created_by_user=creator,
                title=data['title'],
                description=data['description'],
                category=data['category'],
                time_window_text=data.get('time_window_text', ''),
                location_area_text=data.get('location_area_text', ''),
                location_radius_km=data.get('location_radius_km'),
                status=Request.Status.OPEN,
            )

            offers = []
            for offer_data in data.get('offers', []):
                offer = VolunteerOffer.objects.create(
                    request=req,
                    volunteer_user=users[offer_data['volunteer']],
                    message=offer_data.get('message', ''),
                    status=VolunteerOffer.Status.OFFERED,
                )
                offers.append(offer)

            accepted_offer = None
            if data.get('accepted_offer_index') is not None and offers:
                accepted_offer = offers[data['accepted_offer_index']]
                accepted_offer.status = VolunteerOffer.Status.ACCEPTED
                accepted_offer.save(update_fields=['status', 'updated_at'])
                VolunteerOffer.objects.filter(request=req).exclude(id=accepted_offer.id).update(
                    status=VolunteerOffer.Status.REJECTED,
                    updated_at=now,
                )
                req.accepted_offer = accepted_offer

            if data['status'] == Request.Status.IN_PROGRESS:
                req.status = Request.Status.IN_PROGRESS
            elif data['status'] == Request.Status.RESOLVED:
                req.status = Request.Status.RESOLVED
            elif data['status'] == Request.Status.CANCELLED:
                req.status = Request.Status.CANCELLED

            req.save(update_fields=['status', 'accepted_offer', 'updated_at'])

            created_at = now - timedelta(days=data.get('created_days_ago', 30))
            closed_at = None
            if data['status'] in [Request.Status.RESOLVED, Request.Status.CANCELLED]:
                closed_at = now - timedelta(days=data.get('closed_days_ago', 10))
            set_dates(req, created_at, updated_at=closed_at or created_at, closed_at=closed_at)

            if accepted_offer and data.get('messages'):
                conversation = Conversation.objects.create(request=req)
                for msg in data['messages']:
                    sender = users[msg['sender']]
                    message = Message.objects.create(
                        conversation=conversation,
                        sender_user=sender,
                        body=msg['body'],
                    )
                    msg_created = created_at + timedelta(days=msg.get('days_after', 1))
                    Message.objects.filter(id=message.id).update(created_at=msg_created)

            return req

        requests_data = [
            {
                'title': 'Necesito ayuda con la compra semanal',
                'description': 'No puedo salir de casa esta semana por una lesión en la pierna. ¿Alguien podría hacer la compra en el supermercado cercano? Tengo la lista preparada.',
                'category': 'Recados',
                'time_window_text': 'Cualquier día de esta semana por la mañana',
                'location_area_text': 'Zona centro, cerca del mercado municipal',
                'status': Request.Status.OPEN,
                'creator': 'Juan López',
                'created_days_ago': 1,
                'offers': [
                    {'volunteer': 'Laura Gómez', 'message': 'Puedo pasar mañana por la mañana.'},
                    {'volunteer': 'Carlos Navarro', 'message': 'Disponible si lo necesitas.'},
                ],
            },
            {
                'title': 'Acompañamiento al médico',
                'description': 'Tengo cita con el especialista el viernes y me gustaría que alguien me acompañara. No es urgente, pero me sentiría más segura con compañía.',
                'category': 'Acompañamiento',
                'time_window_text': 'Viernes 20 de enero, 11:00',
                'location_area_text': 'Hospital comarcal',
                'status': Request.Status.OPEN,
                'creator': 'Ana Martínez',
                'created_days_ago': 4,
                'offers': [
                    {'volunteer': 'Laura Gómez', 'message': 'Puedo acompañarte si aún necesitas ayuda.'},
                ],
            },
            {
                'title': 'Ayuda con el ordenador',
                'description': 'Mi ordenador va muy lento y no sé qué hacer. ¿Alguien con conocimientos de informática podría echarle un vistazo?',
                'category': 'Tecnología',
                'time_window_text': 'Cualquier tarde',
                'location_area_text': 'Mi domicilio (zona norte)',
                'status': Request.Status.IN_PROGRESS,
                'creator': 'María García',
                'created_days_ago': 6,
                'offers': [
                    {'volunteer': 'Carlos Navarro', 'message': 'Soy técnico jubilado, puedo echarte un vistazo.'},
                    {'volunteer': 'Miguel Santos', 'message': 'Disponible el sábado por la mañana.'},
                ],
                'accepted_offer_index': 0,
                'messages': [
                    {'sender': 'María García', 'body': 'Gracias por ofrecerte. ¿Te viene bien esta tarde?', 'days_after': 1},
                    {'sender': 'Carlos Navarro', 'body': 'Sí, perfecto. Llevo herramientas básicas.', 'days_after': 1},
                ],
            },
            {
                'title': 'Arreglar grifo que gotea',
                'description': 'El grifo de la cocina lleva días goteando. Tengo herramientas básicas pero no sé cómo arreglarlo.',
                'category': 'Hogar',
                'time_window_text': 'Fines de semana',
                'location_area_text': 'Barrio San José',
                'status': Request.Status.OPEN,
                'creator': 'Pedro Sánchez',
                'created_days_ago': 7,
            },
            {
                'title': 'Llevar a mi madre al aeropuerto',
                'description': 'Mi madre tiene que coger un vuelo el sábado a las 7:00 y necesitamos ayuda para llegar con tiempo.',
                'category': 'Transporte',
                'time_window_text': 'Sábado 21 de enero, 5:00',
                'location_area_text': 'Recogida en zona residencial oeste',
                'status': Request.Status.RESOLVED,
                'creator': 'Carmen Ruiz',
                'created_days_ago': 50,
                'closed_days_ago': 40,
                'offers': [
                    {'volunteer': 'Luis Moreno', 'message': 'Puedo llevarla si os va bien.'},
                    {'volunteer': 'Diego Pérez', 'message': 'Tengo coche grande, puedo ayudar.'},
                ],
                'accepted_offer_index': 0,
                'messages': [
                    {'sender': 'Carmen Ruiz', 'body': 'Gracias por ayudar. Confirmamos el punto de recogida.', 'days_after': 2},
                    {'sender': 'Luis Moreno', 'body': 'Perfecto, llego 10 minutos antes.', 'days_after': 2},
                ],
            },
            {
                'title': 'Paseo con perro los fines de semana',
                'description': 'Necesito ayuda para pasear a mi perro algunos sábados por la mañana.',
                'category': 'Acompañamiento',
                'time_window_text': 'Sábados 10:00',
                'location_area_text': 'Parque del río',
                'status': Request.Status.CANCELLED,
                'creator': 'Laura Gómez',
                'created_days_ago': 20,
                'closed_days_ago': 18,
                'offers': [
                    {'volunteer': 'Inés Rodríguez', 'message': 'Podría ayudarte una vez al mes.'},
                ],
            },
            {
                'title': 'Ayuda para instalar impresora',
                'description': 'Necesito ayuda para configurar una impresora doméstica. No logro conectar el wifi.',
                'category': 'Tecnología',
                'time_window_text': 'Martes por la tarde',
                'location_area_text': 'Zona centro',
                'status': Request.Status.RESOLVED,
                'creator': 'Nuria Fernández',
                'created_days_ago': 15,
                'closed_days_ago': 14,
                'offers': [
                    {'volunteer': 'Miguel Santos', 'message': 'Puedo pasar y configurarla.'},
                ],
                'accepted_offer_index': 0,
                'messages': [
                    {'sender': 'Nuria Fernández', 'body': 'Gracias, ¿puedes venir mañana?', 'days_after': 1},
                    {'sender': 'Miguel Santos', 'body': 'Sí, paso después del trabajo.', 'days_after': 1},
                ],
            },
            {
                'title': 'Recoger paquete en correos',
                'description': 'Tengo un aviso para recoger un paquete y no puedo ir en horario de mañana.',
                'category': 'Recados',
                'time_window_text': 'Entre semana por la tarde',
                'location_area_text': 'Oficina de correos central',
                'status': Request.Status.OPEN,
                'creator': 'Inés Rodríguez',
                'created_days_ago': 9,
                'offers': [
                    {'volunteer': 'Juan López', 'message': 'Puedo ayudarte el miércoles.'},
                ],
            },
            {
                'title': 'Acompañamiento a paseo corto',
                'description': 'Me gustaría salir a caminar un rato por la tarde con compañía.',
                'category': 'Acompañamiento',
                'time_window_text': 'Miércoles y jueves por la tarde',
                'location_area_text': 'Paseo del parque',
                'status': Request.Status.IN_PROGRESS,
                'creator': 'Carmen Ruiz',
                'created_days_ago': 6,
                'offers': [
                    {'volunteer': 'Ana Martínez', 'message': 'Me apunto para el jueves.'},
                    {'volunteer': 'Laura Gómez', 'message': 'Puedo ir el miércoles.'},
                ],
                'accepted_offer_index': 1,
                'messages': [
                    {'sender': 'Carmen Ruiz', 'body': 'Gracias, ¿nos vemos a las 18:00?', 'days_after': 1},
                    {'sender': 'Laura Gómez', 'body': 'Perfecto, allí estaré.', 'days_after': 1},
                ],
            },
            {
                'title': 'Revisión de bombillas del portal',
                'description': 'Necesitamos cambiar dos bombillas en el portal. Tengo escalera, pero necesito ayuda.',
                'category': 'Hogar',
                'time_window_text': 'Viernes 19:00',
                'location_area_text': 'Portal 3B, zona sur',
                'status': Request.Status.OPEN,
                'creator': 'Diego Pérez',
                'created_days_ago': 8,
            },
            {
                'title': 'Pequeña mudanza de cajas',
                'description': 'Tengo unas cajas ligeras que necesito mover al trastero del edificio.',
                'category': 'Hogar',
                'time_window_text': 'Sábado por la mañana',
                'location_area_text': 'Calle del Lago',
                'status': Request.Status.OPEN,
                'creator': 'Miguel Santos',
                'created_days_ago': 7,
                'offers': [
                    {'volunteer': 'Pedro Sánchez', 'message': 'Puedo ayudar si es algo ligero.'},
                ],
            },
            {
                'title': 'Cuidado de plantas durante viaje',
                'description': 'Necesito que alguien riegue mis plantas una vez por semana durante julio.',
                'category': 'Hogar',
                'time_window_text': 'Semanal en julio',
                'location_area_text': 'Zona universitaria',
                'status': Request.Status.RESOLVED,
                'creator': 'Laura Gómez',
                'created_days_ago': 5,
                'closed_days_ago': 3,
                'offers': [
                    {'volunteer': 'Nuria Fernández', 'message': 'Puedo pasar los martes.'},
                ],
                'accepted_offer_index': 0,
                'messages': [
                    {'sender': 'Laura Gómez', 'body': 'Gracias, te paso las llaves en persona.', 'days_after': 1},
                    {'sender': 'Nuria Fernández', 'body': 'Perfecto, coordinamos.', 'days_after': 1},
                ],
            },
            {
                'title': 'Acompañamiento al banco',
                'description': 'Necesito compañía para hacer una gestión bancaria sencilla.',
                'category': 'Acompañamiento',
                'time_window_text': 'Mañana por la mañana',
                'location_area_text': 'Zona centro',
                'status': Request.Status.OPEN,
                'creator': 'Carmen Ruiz',
                'created_days_ago': 2,
                'offers': [
                    {'volunteer': 'Ana Martínez', 'message': 'Te acompaño sin problema.'},
                ],
            },
            {
                'title': 'Revisar conexión wifi en casa',
                'description': 'El router no funciona bien y necesito ayuda para configurarlo.',
                'category': 'Tecnología',
                'time_window_text': 'Esta tarde',
                'location_area_text': 'Zona norte',
                'status': Request.Status.OPEN,
                'creator': 'María García',
                'created_days_ago': 5,
                'offers': [
                    {'volunteer': 'Carlos Navarro', 'message': 'Puedo revisarlo contigo.'},
                    {'volunteer': 'Miguel Santos', 'message': 'También puedo pasar.'},
                ],
            },
            {
                'title': 'Llevar documentos al ayuntamiento',
                'description': 'Necesito entregar unos documentos y no puedo desplazarme esta semana.',
                'category': 'Recados',
                'time_window_text': 'Antes del viernes',
                'location_area_text': 'Plaza del ayuntamiento',
                'status': Request.Status.OPEN,
                'creator': 'Luis Moreno',
                'created_days_ago': 9,
                'offers': [
                    {'volunteer': 'Juan López', 'message': 'Puedo hacerlo mañana.'},
                ],
            },
            {
                'title': 'Ayuda con formulario online',
                'description': 'No consigo completar un trámite digital y necesito apoyo.',
                'category': 'Tecnología',
                'time_window_text': 'Hoy por la tarde',
                'location_area_text': 'Barrio universitario',
                'status': Request.Status.OPEN,
                'creator': 'Nuria Fernández',
                'created_days_ago': 4,
                'offers': [
                    {'volunteer': 'Carlos Navarro', 'message': 'Te ayudo en un rato.'},
                ],
            },
            {
                'title': 'Traslado a fisioterapia',
                'description': 'Necesito que alguien me acerque al centro de fisioterapia.',
                'category': 'Transporte',
                'time_window_text': 'Martes 10:00',
                'location_area_text': 'Zona centro',
                'status': Request.Status.OPEN,
                'creator': 'Juan López',
                'created_days_ago': 10,
                'offers': [
                    {'volunteer': 'Diego Pérez', 'message': 'Te puedo llevar en coche.'},
                    {'volunteer': 'Luis Moreno', 'message': 'También estoy disponible.'},
                ],
            },
            {
                'title': 'Configurar cuenta de correo',
                'description': 'No consigo dejar bien configurado el correo en móvil y portátil.',
                'category': 'Tecnología',
                'time_window_text': 'Durante la semana por la tarde',
                'location_area_text': 'Barrio de la estación',
                'status': Request.Status.IN_PROGRESS,
                'creator': 'Inés Rodríguez',
                'created_days_ago': 8,
                'offers': [
                    {'volunteer': 'Nuria Fernández', 'message': 'Te ayudo con la configuración.'},
                    {'volunteer': 'María García', 'message': 'Si quieres, también paso luego.'},
                ],
                'accepted_offer_index': 0,
                'messages': [
                    {'sender': 'Inés Rodríguez', 'body': 'Gracias, ¿podemos verlo hoy?', 'days_after': 1},
                    {'sender': 'Nuria Fernández', 'body': 'Sí, esta tarde va bien.', 'days_after': 1},
                ],
            },
            {
                'title': 'Montar mueble del salón',
                'description': 'Necesito ayuda para montar un mueble pequeño que acabo de comprar.',
                'category': 'Hogar',
                'time_window_text': 'Sábado por la mañana',
                'location_area_text': 'Barrio norte',
                'status': Request.Status.IN_PROGRESS,
                'creator': 'Pedro Sánchez',
                'created_days_ago': 9,
                'offers': [
                    {'volunteer': 'Diego Pérez', 'message': 'Llevo herramientas y te ayudo.'},
                    {'volunteer': 'Luis Moreno', 'message': 'Si hace falta otra mano, voy.'},
                ],
                'accepted_offer_index': 0,
                'messages': [
                    {'sender': 'Pedro Sánchez', 'body': 'Quedamos el sábado a las 10:00.', 'days_after': 1},
                    {'sender': 'Diego Pérez', 'body': 'Perfecto, allí estaré.', 'days_after': 1},
                ],
            },
            {
                'title': 'Traslado al hospital para consulta',
                'description': 'Tengo una cita programada y necesito ayuda con el desplazamiento.',
                'category': 'Transporte',
                'time_window_text': 'Jueves 9:00',
                'location_area_text': 'Hospital comarcal',
                'status': Request.Status.IN_PROGRESS,
                'creator': 'Ana Martínez',
                'created_days_ago': 7,
                'offers': [
                    {'volunteer': 'Juan López', 'message': 'Puedo llevarte y recogerte.'},
                    {'volunteer': 'Luis Moreno', 'message': 'También estoy disponible.'},
                ],
                'accepted_offer_index': 1,
                'messages': [
                    {'sender': 'Ana Martínez', 'body': '¿Te viene bien a las 8:30?', 'days_after': 1},
                    {'sender': 'Luis Moreno', 'body': 'Sí, te recojo sin problema.', 'days_after': 1},
                ],
            },
            {
                'title': 'Compra grande para la semana',
                'description': 'Necesito ayuda para traer una compra pesada desde el supermercado.',
                'category': 'Recados',
                'time_window_text': 'Viernes por la tarde',
                'location_area_text': 'Mercado municipal',
                'status': Request.Status.IN_PROGRESS,
                'creator': 'Laura Gómez',
                'created_days_ago': 4,
                'offers': [
                    {'volunteer': 'María García', 'message': 'Te acompaño a comprar.'},
                    {'volunteer': 'Inés Rodríguez', 'message': 'Yo ayudo con las bolsas.'},
                    {'volunteer': 'Carmen Ruiz', 'message': 'Si quieres, voy en coche.'},
                ],
                'accepted_offer_index': 2,
                'messages': [
                    {'sender': 'Laura Gómez', 'body': 'Gracias, mejor en coche.', 'days_after': 1},
                    {'sender': 'Carmen Ruiz', 'body': 'Perfecto, te recojo a las 18:00.', 'days_after': 1},
                ],
            },
            {
                'title': 'Acompañamiento para trámite',
                'description': 'Tengo que hacer una gestión administrativa y prefiero no ir solo.',
                'category': 'Acompañamiento',
                'time_window_text': 'Lunes por la mañana',
                'location_area_text': 'Oficina de la seguridad social',
                'status': Request.Status.IN_PROGRESS,
                'creator': 'Juan López',
                'created_days_ago': 10,
                'offers': [
                    {'volunteer': 'Ana Martínez', 'message': 'Puedo ir contigo.'},
                    {'volunteer': 'Carlos Navarro', 'message': 'Si hace falta, me acerco.'},
                ],
                'accepted_offer_index': 0,
                'messages': [
                    {'sender': 'Juan López', 'body': '¿Quedamos media hora antes?', 'days_after': 1},
                    {'sender': 'Ana Martínez', 'body': 'Sí, mejor así vamos con tiempo.', 'days_after': 2},
                ],
            },
            {
                'title': 'Mover lavadora al trastero',
                'description': 'Necesito ayuda para mover una lavadora al trastero del edificio.',
                'category': 'Hogar',
                'time_window_text': 'Sábado por la mañana',
                'location_area_text': 'Bloque residencial oeste',
                'status': Request.Status.IN_PROGRESS,
                'creator': 'Diego Pérez',
                'created_days_ago': 12,
                'offers': [
                    {'volunteer': 'Pedro Sánchez', 'message': 'Tengo carro para mover peso.'},
                    {'volunteer': 'Miguel Santos', 'message': 'Yo también puedo echar una mano.'},
                ],
                'accepted_offer_index': 1,
                'messages': [
                    {'sender': 'Diego Pérez', 'body': 'Lo hacemos el sábado a las 9:30.', 'days_after': 1},
                    {'sender': 'Miguel Santos', 'body': 'De acuerdo, llevo guantes.', 'days_after': 2},
                ],
            },
            {
                'title': 'Pintar valla comunitaria',
                'description': 'Necesitábamos ayuda para pintar la valla del patio.',
                'category': 'Hogar',
                'time_window_text': 'Sábado por la mañana',
                'location_area_text': 'Patio comunitario',
                'status': Request.Status.RESOLVED,
                'creator': 'Pedro Sánchez',
                'created_days_ago': 90,
                'closed_days_ago': 76,
                'offers': [
                    {'volunteer': 'Juan López', 'message': 'Llevo material de pintura.'},
                    {'volunteer': 'Diego Pérez', 'message': 'Yo también me apunto.'},
                ],
                'accepted_offer_index': 1,
                'messages': [
                    {'sender': 'Pedro Sánchez', 'body': 'Quedamos a las 9:00.', 'days_after': 2},
                    {'sender': 'Diego Pérez', 'body': 'Allí estaré.', 'days_after': 3},
                ],
            },
            {
                'title': 'Ayuda con tablet para trámites',
                'description': 'Necesitaba apoyo para realizar trámites online en una tablet.',
                'category': 'Tecnología',
                'time_window_text': 'Tarde',
                'location_area_text': 'Barrio de la estación',
                'status': Request.Status.RESOLVED,
                'creator': 'Inés Rodríguez',
                'created_days_ago': 85,
                'closed_days_ago': 74,
                'offers': [
                    {'volunteer': 'Nuria Fernández', 'message': 'Te ayudo con todos los pasos.'},
                    {'volunteer': 'Miguel Santos', 'message': 'Si hace falta, también paso.'},
                ],
                'accepted_offer_index': 0,
                'messages': [
                    {'sender': 'Inés Rodríguez', 'body': 'Ya quedó todo enviado, gracias.', 'days_after': 2},
                    {'sender': 'Nuria Fernández', 'body': 'Me alegro, perfecto.', 'days_after': 3},
                ],
            },
            {
                'title': 'Compra de mercado mensual',
                'description': 'Se necesitaba apoyo para una compra mensual de productos pesados.',
                'category': 'Recados',
                'time_window_text': 'Mañana',
                'location_area_text': 'Mercado municipal',
                'status': Request.Status.RESOLVED,
                'creator': 'Juan López',
                'created_days_ago': 180,
                'closed_days_ago': 170,
                'offers': [
                    {'volunteer': 'Laura Gómez', 'message': 'Puedo ayudar con el carro.'},
                    {'volunteer': 'Carlos Navarro', 'message': 'Si hace falta coche, avísame.'},
                ],
                'accepted_offer_index': 1,
                'messages': [
                    {'sender': 'Juan López', 'body': 'Tu coche fue clave, gracias.', 'days_after': 2},
                    {'sender': 'Carlos Navarro', 'body': 'Cuando quieras repetimos.', 'days_after': 3},
                ],
            },
            {
                'title': 'Reparación de enchufe en cocina',
                'description': 'Se solucionó un problema en un enchufe de la cocina.',
                'category': 'Hogar',
                'time_window_text': 'Durante la semana',
                'location_area_text': 'Zona norte',
                'status': Request.Status.RESOLVED,
                'creator': 'María García',
                'created_days_ago': 140,
                'closed_days_ago': 128,
                'offers': [
                    {'volunteer': 'Carlos Navarro', 'message': 'Puedo revisarlo con seguridad.'},
                    {'volunteer': 'Pedro Sánchez', 'message': 'También puedo ayudar.'},
                ],
                'accepted_offer_index': 1,
                'messages': [
                    {'sender': 'María García', 'body': 'Gracias por venir tan rápido.', 'days_after': 1},
                    {'sender': 'Pedro Sánchez', 'body': 'Ya quedó resuelto.', 'days_after': 2},
                ],
            },
            {
                'title': 'Acompañamiento a consulta especialista',
                'description': 'Necesitaba compañía para una consulta y todo salió bien.',
                'category': 'Acompañamiento',
                'time_window_text': 'Miércoles 11:00',
                'location_area_text': 'Hospital comarcal',
                'status': Request.Status.RESOLVED,
                'creator': 'Ana Martínez',
                'created_days_ago': 75,
                'closed_days_ago': 68,
                'offers': [
                    {'volunteer': 'Laura Gómez', 'message': 'Te acompaño sin problema.'},
                    {'volunteer': 'Carmen Ruiz', 'message': 'Si hace falta, también puedo.'},
                ],
                'accepted_offer_index': 0,
                'messages': [
                    {'sender': 'Ana Martínez', 'body': 'Gracias por acompañarme.', 'days_after': 1},
                    {'sender': 'Laura Gómez', 'body': 'Encantada de ayudarte.', 'days_after': 2},
                ],
            },
            {
                'title': 'Limpieza puntual de trastero',
                'description': 'Se iba a hacer limpieza del trastero, pero se aplazó y se canceló.',
                'category': 'Hogar',
                'time_window_text': 'Sábado por la mañana',
                'location_area_text': 'Trasteros del bloque A',
                'status': Request.Status.CANCELLED,
                'creator': 'Diego Pérez',
                'created_days_ago': 32,
                'closed_days_ago': 27,
                'offers': [
                    {'volunteer': 'Pedro Sánchez', 'message': 'Puedo ayudarte con la limpieza.'},
                    {'volunteer': 'Miguel Santos', 'message': 'Yo también me apunto.'},
                ],
            },
            {
                'title': 'Recogida urgente de paquete',
                'description': 'Era una recogida urgente, pero se resolvió por otra vía y se canceló.',
                'category': 'Recados',
                'time_window_text': 'Hoy',
                'location_area_text': 'Punto de mensajería del barrio',
                'status': Request.Status.CANCELLED,
                'creator': 'Luis Moreno',
                'created_days_ago': 40,
                'closed_days_ago': 35,
                'offers': [
                    {'volunteer': 'Juan López', 'message': 'Puedo pasar a primera hora.'},
                ],
            },
            {
                'title': 'Traslado al aeropuerto de madrugada',
                'description': 'Se pidió ayuda para traslado, pero cambió el plan y se canceló.',
                'category': 'Transporte',
                'time_window_text': 'Madrugada',
                'location_area_text': 'Zona sur',
                'status': Request.Status.CANCELLED,
                'creator': 'Ana Martínez',
                'created_days_ago': 55,
                'closed_days_ago': 49,
                'offers': [
                    {'volunteer': 'Diego Pérez', 'message': 'Puedo llevarte en coche.'},
                    {'volunteer': 'Luis Moreno', 'message': 'También me puedo encargar.'},
                ],
            },
            {
                'title': 'Mover muebles de una habitación',
                'description': 'Se quería reorganizar una habitación, pero se aplazó y se canceló.',
                'category': 'Hogar',
                'time_window_text': 'Sábado por la tarde',
                'location_area_text': 'Barrio de la estación',
                'status': Request.Status.CANCELLED,
                'creator': 'Nuria Fernández',
                'created_days_ago': 28,
                'closed_days_ago': 24,
                'offers': [
                    {'volunteer': 'Juan López', 'message': 'Te ayudo a moverlos.'},
                    {'volunteer': 'Laura Gómez', 'message': 'También me acerco.'},
                ],
            },
        ]

        requests_data_com_vecinos = [
            {
                'community': 'Com. Vecinos',
                'title': 'Traslado al centro de día',
                'description': 'Necesito apoyo para llevar a un familiar al centro de día y volver.',
                'category': 'Transporte',
                'time_window_text': 'Mañana 9:00',
                'location_area_text': 'Com. Vecinos - zona principal',
                'status': Request.Status.OPEN,
                'creator': 'Carmen Ruiz',
                'created_days_ago': 2,
                'offers': [
                    {'volunteer': 'Luis Moreno', 'message': 'Puedo llevaros en coche.'},
                    {'volunteer': 'Diego Pérez', 'message': 'Si hace falta, me encargo yo.'},
                ],
            },
            {
                'community': 'Com. Vecinos',
                'title': 'Configurar teléfono para videollamadas',
                'description': 'Necesito ayuda para dejar un móvil preparado para videollamadas familiares.',
                'category': 'Tecnología',
                'time_window_text': 'Esta tarde',
                'location_area_text': 'Com. Vecinos - bloque B',
                'status': Request.Status.OPEN,
                'creator': 'Laura Gómez',
                'created_days_ago': 4,
                'offers': [
                    {'volunteer': 'Nuria Fernández', 'message': 'Te ayudo con toda la configuración.'},
                ],
            },
            {
                'community': 'Com. Vecinos',
                'title': 'Acompañamiento a revisión médica',
                'description': 'Tengo una revisión y me gustaría ir acompañada para mayor tranquilidad.',
                'category': 'Acompañamiento',
                'time_window_text': 'Viernes 11:30',
                'location_area_text': 'Centro de salud de barrio',
                'status': Request.Status.IN_PROGRESS,
                'creator': 'Ana Martínez',
                'created_days_ago': 6,
                'offers': [
                    {'volunteer': 'Laura Gómez', 'message': 'Te acompaño sin problema.'},
                    {'volunteer': 'Miguel Santos', 'message': 'Si hace falta, también puedo ir.'},
                ],
                'accepted_offer_index': 0,
                'messages': [
                    {'sender': 'Ana Martínez', 'body': 'Gracias, quedamos media hora antes.', 'days_after': 1},
                    {'sender': 'Laura Gómez', 'body': 'Perfecto, allí estaré.', 'days_after': 1},
                ],
            },
            {
                'community': 'Com. Vecinos',
                'title': 'Subir cajas al altillo',
                'description': 'Necesito ayuda para subir unas cajas ligeras al altillo del trastero.',
                'category': 'Hogar',
                'time_window_text': 'Sábado por la mañana',
                'location_area_text': 'Com. Vecinos - trasteros',
                'status': Request.Status.IN_PROGRESS,
                'creator': 'Miguel Santos',
                'created_days_ago': 8,
                'offers': [
                    {'volunteer': 'Diego Pérez', 'message': 'Puedo ayudarte con eso.'},
                    {'volunteer': 'Luis Moreno', 'message': 'Cuenta conmigo si hace falta.'},
                ],
                'accepted_offer_index': 1,
                'messages': [
                    {'sender': 'Miguel Santos', 'body': 'Luis, ¿te viene bien el sábado?', 'days_after': 1},
                    {'sender': 'Luis Moreno', 'body': 'Sí, a primera hora perfecto.', 'days_after': 2},
                ],
            },
            {
                'community': 'Com. Vecinos',
                'title': 'Compra semanal completada',
                'description': 'La ayuda para la compra semanal ya se completó correctamente.',
                'category': 'Recados',
                'time_window_text': 'Entre semana',
                'location_area_text': 'Com. Vecinos - zona comercial',
                'status': Request.Status.RESOLVED,
                'creator': 'Luis Moreno',
                'created_days_ago': 70,
                'closed_days_ago': 61,
                'offers': [
                    {'volunteer': 'Carmen Ruiz', 'message': 'Puedo acompañarte al supermercado.'},
                    {'volunteer': 'Ana Martínez', 'message': 'También puedo ayudar con bolsas.'},
                ],
                'accepted_offer_index': 0,
                'messages': [
                    {'sender': 'Luis Moreno', 'body': 'Gracias por la ayuda con la compra.', 'days_after': 1},
                    {'sender': 'Carmen Ruiz', 'body': 'Encantada, cuando quieras repetimos.', 'days_after': 2},
                ],
            },
            {
                'community': 'Com. Vecinos',
                'title': 'Revisión de portátil finalizada',
                'description': 'La revisión del portátil ya quedó completada y funcionando correctamente.',
                'category': 'Tecnología',
                'time_window_text': 'Tardes',
                'location_area_text': 'Com. Vecinos - bloque C',
                'status': Request.Status.RESOLVED,
                'creator': 'Nuria Fernández',
                'created_days_ago': 95,
                'closed_days_ago': 86,
                'offers': [
                    {'volunteer': 'Miguel Santos', 'message': 'Puedo revisarlo y optimizarlo.'},
                ],
                'accepted_offer_index': 0,
                'messages': [
                    {'sender': 'Nuria Fernández', 'body': 'Ya va mucho mejor, gracias.', 'days_after': 2},
                    {'sender': 'Miguel Santos', 'body': 'Genial, me alegro.', 'days_after': 3},
                ],
            },
            {
                'community': 'Com. Vecinos',
                'title': 'Paseo cancelado por lluvia',
                'description': 'La salida prevista se canceló por mal tiempo y se reprogramará más adelante.',
                'category': 'Acompañamiento',
                'time_window_text': 'Tarde',
                'location_area_text': 'Com. Vecinos - plaza interior',
                'status': Request.Status.CANCELLED,
                'creator': 'Carmen Ruiz',
                'created_days_ago': 19,
                'closed_days_ago': 16,
                'offers': [
                    {'volunteer': 'Ana Martínez', 'message': 'Si mejora el tiempo, me apunto.'},
                ],
            },
            {
                'community': 'Com. Vecinos',
                'title': 'Traslado cancelado por cambio de cita',
                'description': 'El traslado ya no es necesario porque cambiaron la fecha de la cita.',
                'category': 'Transporte',
                'time_window_text': 'Mañana',
                'location_area_text': 'Com. Vecinos - acceso principal',
                'status': Request.Status.CANCELLED,
                'creator': 'Laura Gómez',
                'created_days_ago': 24,
                'closed_days_ago': 19,
                'offers': [
                    {'volunteer': 'Diego Pérez', 'message': 'Puedo llevarte si lo retomas.'},
                    {'volunteer': 'Luis Moreno', 'message': 'También estoy disponible.'},
                ],
            },
        ]

        created_requests = []
        for data in requests_data:
            created_requests.append(create_request(data))
        com_vecinos_start_index = len(created_requests)
        for data in requests_data_com_vecinos:
            created_requests.append(create_request(data))

        reports_data = [
            {
                'reporter': 'María García',
                'request_index': 0,
                'reason': Report.Reason.OTHER,
                'description': 'Contenido poco claro, se solicita revisión.',
            },
            {
                'reporter': 'Carlos Navarro',
                'request_index': 3,
                'reason': Report.Reason.ADVERTISING,
                'description': 'Parece invitar a contratar servicios externos.',
            },
            {
                'reporter': 'Ana Martínez',
                'request_index': 5,
                'reason': Report.Reason.PROHIBITED_CONTENT,
                'description': 'Hay partes del texto que no encajan con las normas.',
            },
            {
                'reporter': 'Luis Moreno',
                'request_index': 8,
                'reason': Report.Reason.PAYMENTS,
                'description': 'Se sugiere compensación económica por la ayuda.',
            },
            {
                'reporter': 'Nuria Fernández',
                'request_index': 10,
                'reason': Report.Reason.OTHER,
                'description': 'Revisión preventiva de moderación.',
            },
            {
                'reporter': 'Inés Rodríguez',
                'request_index': 13,
                'reason': Report.Reason.HARASSMENT,
                'description': 'El tono de los mensajes no parece adecuado.',
            },
            {
                'reporter': 'Juan López',
                'request_index': 15,
                'reason': Report.Reason.PAYMENTS,
                'description': 'Se menciona un posible pago por el apoyo.',
            },
            {
                'reporter': 'Laura Gómez',
                'request_index': 17,
                'reason': Report.Reason.ADVERTISING,
                'description': 'Puede haber intención de promoción comercial.',
            },
            {
                'reporter': 'Diego Pérez',
                'request_index': 20,
                'reason': Report.Reason.OTHER,
                'description': 'Se solicita revisión del contenido publicado.',
            },
            {
                'reporter': 'Miguel Santos',
                'request_index': 23,
                'reason': Report.Reason.PROHIBITED_CONTENT,
                'description': 'El formato no encaja con el uso permitido.',
            },
            {
                'reporter': 'Carmen Ruiz',
                'request_index': 27,
                'reason': Report.Reason.OTHER,
                'description': 'Reporte informativo para revisión del equipo.',
            },
            {
                'reporter': 'Pedro Sánchez',
                'request_index': 30,
                'reason': Report.Reason.ADVERTISING,
                'description': 'Parece mensaje de captación de servicios.',
            },
            {
                'reporter': 'Laura Gómez',
                'request_index': com_vecinos_start_index + 0,
                'reason': Report.Reason.OTHER,
                'description': 'Se solicita revisión de contenido por dudas.',
            },
            {
                'reporter': 'Miguel Santos',
                'request_index': com_vecinos_start_index + 2,
                'reason': Report.Reason.HARASSMENT,
                'description': 'Se detecta tono inadecuado en el intercambio.',
            },
            {
                'reporter': 'Ana Martínez',
                'request_index': com_vecinos_start_index + 4,
                'reason': Report.Reason.PAYMENTS,
                'description': 'Se insinúa compensación económica no permitida.',
            },
            {
                'reporter': 'Nuria Fernández',
                'request_index': com_vecinos_start_index + 7,
                'reason': Report.Reason.ADVERTISING,
                'description': 'Puede haber intención de promoción comercial.',
            },
        ]

        created_reports = []
        for report_data in reports_data:
            idx = report_data['request_index']
            if idx < 0 or idx >= len(created_requests):
                continue
            created_reports.append(
                Report.objects.create(
                    reporter_user=users[report_data['reporter']],
                    request=created_requests[idx],
                    reason=report_data['reason'],
                    description=report_data['description'],
                )
            )

        def set_loan_item_dates(item, created_at, updated_at=None, loaned_at=None, returned_at=None):
            if updated_at is None:
                updated_at = created_at
            LoanItem.objects.filter(id=item.id).update(
                created_at=created_at,
                updated_at=updated_at,
                loaned_at=loaned_at,
                returned_at=returned_at,
            )

        def set_loan_request_dates(loan_request, created_at, updated_at=None, responded_at=None):
            if updated_at is None:
                updated_at = responded_at or created_at
            LoanRequest.objects.filter(id=loan_request.id).update(
                created_at=created_at,
                updated_at=updated_at,
                responded_at=responded_at,
            )

        def create_loan_item(data):
            owner = users[data['owner']]
            community = communities_by_name[data.get('community', 'Obanos')]
            item = LoanItem.objects.create(
                community=community,
                owner_user=owner,
                title=data['title'],
                description=data.get('description', ''),
                status=LoanItem.Status.AVAILABLE,
            )

            created_at = now - timedelta(days=data.get('created_days_ago', 5))
            updated_at = created_at
            item_requests = []

            for req_data in data.get('requests', []):
                loan_request = LoanRequest.objects.create(
                    item=item,
                    requester_user=users[req_data['requester']],
                    message=req_data.get('message', ''),
                    status=req_data.get('status', LoanRequest.Status.PENDING),
                )
                req_created_days = req_data.get('created_days_ago', max(data.get('created_days_ago', 5) - 1, 0))
                req_created_at = now - timedelta(days=req_created_days)
                responded_at = None
                if loan_request.status != LoanRequest.Status.PENDING:
                    default_responded_days = max(req_created_days - 1, 0)
                    responded_days = req_data.get('responded_days_ago', default_responded_days)
                    responded_at = now - timedelta(days=responded_days)
                req_updated_at = responded_at or req_created_at
                set_loan_request_dates(loan_request, req_created_at, req_updated_at, responded_at)
                item_requests.append(loan_request)
                if req_updated_at > updated_at:
                    updated_at = req_updated_at

            if data.get('status') == LoanItem.Status.LOANED:
                borrower = users[data['borrower']]
                loaned_at = now - timedelta(days=data.get('loaned_days_ago', 1))
                item.status = LoanItem.Status.LOANED
                item.borrower_user = borrower
                item.loaned_at = loaned_at
                item.returned_at = None
                item.save(update_fields=['status', 'borrower_user', 'loaned_at', 'returned_at', 'updated_at'])

                accepted_request = None
                for loan_request in item_requests:
                    if loan_request.requester_user_id == borrower.id:
                        accepted_request = loan_request
                        break

                if accepted_request is None:
                    accepted_request = LoanRequest.objects.create(
                        item=item,
                        requester_user=borrower,
                        message='Solicitud aceptada en demo.',
                        status=LoanRequest.Status.ACCEPTED,
                    )
                    set_loan_request_dates(
                        accepted_request,
                        loaned_at - timedelta(hours=3),
                        loaned_at,
                        loaned_at,
                    )
                    item_requests.append(accepted_request)

                LoanRequest.objects.filter(id=accepted_request.id).update(
                    status=LoanRequest.Status.ACCEPTED,
                    responded_at=loaned_at,
                    updated_at=loaned_at,
                )
                LoanRequest.objects.filter(item=item, status=LoanRequest.Status.PENDING).exclude(id=accepted_request.id).update(
                    status=LoanRequest.Status.REJECTED,
                    responded_at=loaned_at,
                    updated_at=loaned_at,
                )
                if loaned_at > updated_at:
                    updated_at = loaned_at
                set_loan_item_dates(item, created_at, updated_at=updated_at, loaned_at=loaned_at, returned_at=None)
            else:
                set_loan_item_dates(item, created_at, updated_at=updated_at)

            return item

        loan_items_data = [
            {
                'community': 'Obanos',
                'title': 'Taladro percutor',
                'description': 'Taladro con juego de brocas para pared y madera.',
                'owner': 'Carlos Navarro',
                'status': LoanItem.Status.AVAILABLE,
                'created_days_ago': 2,
                'requests': [
                    {
                        'requester': 'Juan López',
                        'message': 'Lo necesitaría para colgar unas baldas esta tarde.',
                        'status': LoanRequest.Status.PENDING,
                        'created_days_ago': 1,
                    },
                ],
            },
            {
                'community': 'Obanos',
                'title': 'Escalera plegable',
                'description': 'Escalera de aluminio de 4 peldaños.',
                'owner': 'Pedro Sánchez',
                'status': LoanItem.Status.LOANED,
                'borrower': 'María García',
                'created_days_ago': 6,
                'loaned_days_ago': 1,
                'requests': [
                    {
                        'requester': 'María García',
                        'message': 'La necesito para cambiar una lámpara.',
                        'status': LoanRequest.Status.PENDING,
                        'created_days_ago': 2,
                    },
                    {
                        'requester': 'Inés Rodríguez',
                        'message': 'Si no se usa esta semana, me vendría bien.',
                        'status': LoanRequest.Status.PENDING,
                        'created_days_ago': 2,
                    },
                ],
            },
            {
                'community': 'Obanos',
                'title': 'Silla de ruedas plegable',
                'description': 'Para traslados puntuales dentro del barrio.',
                'owner': 'Carmen Ruiz',
                'status': LoanItem.Status.AVAILABLE,
                'created_days_ago': 3,
                'requests': [
                    {
                        'requester': 'Ana Martínez',
                        'message': 'La necesitaría para una cita médica.',
                        'status': LoanRequest.Status.PENDING,
                        'created_days_ago': 1,
                    },
                ],
            },
            {
                'community': 'Obanos',
                'title': 'Juego de llaves Allen',
                'description': 'Set completo para ajustes de muebles y bicicletas.',
                'owner': 'Miguel Santos',
                'status': LoanItem.Status.LOANED,
                'borrower': 'Juan López',
                'created_days_ago': 8,
                'loaned_days_ago': 2,
                'requests': [
                    {
                        'requester': 'Juan López',
                        'message': 'Tengo que apretar una silla y una mesa.',
                        'status': LoanRequest.Status.PENDING,
                        'created_days_ago': 3,
                    },
                ],
            },
            {
                'community': 'Obanos',
                'title': 'Carretilla pequeña',
                'description': 'Ideal para mover cajas del portal al trastero.',
                'owner': 'Inés Rodríguez',
                'status': LoanItem.Status.AVAILABLE,
                'created_days_ago': 1,
            },
            {
                'community': 'Obanos',
                'title': 'Kit de destornilladores',
                'description': 'Plano, estrella y precisión.',
                'owner': 'Laura Gómez',
                'status': LoanItem.Status.AVAILABLE,
                'created_days_ago': 4,
                'requests': [
                    {
                        'requester': 'Pedro Sánchez',
                        'message': 'Me vendrían bien para un ajuste rápido en casa.',
                        'status': LoanRequest.Status.PENDING,
                        'created_days_ago': 2,
                    },
                ],
            },
            {
                'community': 'Com. Vecinos',
                'title': 'Aspiradora de mano',
                'description': 'Para limpiezas rápidas en coche o sofá.',
                'owner': 'Laura Gómez',
                'status': LoanItem.Status.AVAILABLE,
                'created_days_ago': 2,
                'requests': [
                    {
                        'requester': 'Diego Pérez',
                        'message': 'La usaría para limpiar el coche este finde.',
                        'status': LoanRequest.Status.PENDING,
                        'created_days_ago': 1,
                    },
                ],
            },
            {
                'community': 'Com. Vecinos',
                'title': 'Taladro inalámbrico',
                'description': 'Incluye batería extra y cargador.',
                'owner': 'Luis Moreno',
                'status': LoanItem.Status.LOANED,
                'borrower': 'Ana Martínez',
                'created_days_ago': 5,
                'loaned_days_ago': 1,
                'requests': [
                    {
                        'requester': 'Ana Martínez',
                        'message': 'Lo necesito para fijar una estantería.',
                        'status': LoanRequest.Status.PENDING,
                        'created_days_ago': 2,
                    },
                    {
                        'requester': 'Carmen Ruiz',
                        'message': 'Si queda libre la semana que viene, avísame.',
                        'status': LoanRequest.Status.PENDING,
                        'created_days_ago': 2,
                    },
                ],
            },
            {
                'community': 'Com. Vecinos',
                'title': 'Sillas plegables (x2)',
                'description': 'Dos sillas para visita puntual o evento de comunidad.',
                'owner': 'Carmen Ruiz',
                'status': LoanItem.Status.AVAILABLE,
                'created_days_ago': 3,
            },
            {
                'community': 'Com. Vecinos',
                'title': 'Cargador universal portátil',
                'description': 'Compatible con varios móviles y tablets.',
                'owner': 'Nuria Fernández',
                'status': LoanItem.Status.AVAILABLE,
                'created_days_ago': 1,
                'requests': [
                    {
                        'requester': 'Miguel Santos',
                        'message': 'Lo necesito para una salida larga mañana.',
                        'status': LoanRequest.Status.PENDING,
                        'created_days_ago': 1,
                    },
                ],
            },
            {
                'community': 'Com. Vecinos',
                'title': 'Mini escalera de hogar',
                'description': 'Escalera compacta para tareas ligeras.',
                'owner': 'Diego Pérez',
                'status': LoanItem.Status.LOANED,
                'borrower': 'Carmen Ruiz',
                'created_days_ago': 7,
                'loaned_days_ago': 2,
                'requests': [
                    {
                        'requester': 'Carmen Ruiz',
                        'message': 'La usaré para organizar armarios.',
                        'status': LoanRequest.Status.PENDING,
                        'created_days_ago': 3,
                    },
                ],
            },
            {
                'community': 'Com. Vecinos',
                'title': 'Carro de compra plegable',
                'description': 'Muy útil para compras con bolsas pesadas.',
                'owner': 'Ana Martínez',
                'status': LoanItem.Status.AVAILABLE,
                'created_days_ago': 2,
                'requests': [
                    {
                        'requester': 'Luis Moreno',
                        'message': 'Me vendría bien para la compra del viernes.',
                        'status': LoanRequest.Status.PENDING,
                        'created_days_ago': 1,
                    },
                ],
            },
        ]

        created_loan_items = [create_loan_item(data) for data in loan_items_data]

        self.stdout.write(self.style.SUCCESS('Datos demo ampliados cargados.'))
        self.stdout.write(
            f'Usuarios: {len(demo_users)} | '
            f'Peticiones: {len(created_requests)} | '
            f'Reportes: {len(created_reports)} | '
            f'Items préstamo: {len(created_loan_items)}'
        )
        self.stdout.write(
            f'Obanos: {Request.objects.filter(community=obanos).count()} peticiones | '
            f'Com. Vecinos: {Request.objects.filter(community=com_vecinos).count()} peticiones'
        )
        self.stdout.write(
            f'Préstamos -> Obanos: {LoanItem.objects.filter(community=obanos).count()} items | '
            f'Com. Vecinos: {LoanItem.objects.filter(community=com_vecinos).count()} items'
        )
        self.stdout.write(
            'Superadmin demo: admin@example.com / AdminDemo1234! (solo entorno demo)'
        )
