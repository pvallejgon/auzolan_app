from datetime import timedelta
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.communities.models import Community, Membership
from apps.profiles.models import Profile
from apps.requests.models import Request, VolunteerOffer
from apps.chat.models import Conversation, Message
from apps.reports.models import Report

User = get_user_model()


class Command(BaseCommand):
    help = 'Carga datos de demo para el MVP.'

    def handle(self, *args, **options):
        now = timezone.now()

        community, _ = Community.objects.get_or_create(
            name='Comunidad Demo',
            defaults={'description': 'Comunidad por defecto para el MVP.'},
        )

        # Limpia datos previos en la comunidad demo
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
            Membership.objects.update_or_create(
                user=user,
                community=community,
                defaults={
                    'status': Membership.Status.APPROVED,
                    'role_in_community': Membership.Role.MEMBER,
                    'joined_at': now - timedelta(days=800),
                },
            )
            users[display_name] = user

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

        created_requests = []
        for data in requests_data:
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

        self.stdout.write(self.style.SUCCESS('Datos demo ampliados cargados.'))
        self.stdout.write(
            f'Usuarios: {len(demo_users)} | '
            f'Peticiones: {len(created_requests)} | '
            f'Reportes: {len(created_reports)}'
        )
