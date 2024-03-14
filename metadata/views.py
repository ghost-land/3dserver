from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from shopdeck import settings
from shopdeckdb.models import *
from django.core.exceptions import ObjectDoesNotExist
from urllib.parse import unquote
import datetime
from PIL import Image
import requests
from io import BytesIO

print("Metadata Starting Up")

# Définissez la fonction pour générer les miniatures
def generate_thumbnail(url):
    response = requests.get(url)
    image = Image.open(BytesIO(response.content))
    image.thumbnail((112, 112))
    return image

#La partie "actualité"
@csrf_exempt
def news(request, region):
    news = announcement.objects.all().order_by("-date")
    allnews = []
    for ann in news:
        ann.content = ann.content.replace("\\n", "\n")
        if ann.is_banner:
            ann.content = "(banner:1)"+ann.content
        result = {"headline": ann.title, "description": ann.content, "date":int(ann.date.timestamp())}
        if ann.is_banner:
            result.update(images={
                "image":[{
                "index": 1, 
                "type": "banner", 
                "url": ann.banner_url, 
                "height": 126, 
                "width": 300}]})
        result.update(id=ann.id)
        allnews.append(result)
    res = {"news": {"news_entry": allnews, "length": len(allnews)}}
    return JsonResponse(res)

#Les pharses qui passent sur l'ecran du haut
@csrf_exempt
def telops(request, region):
    motds = motd.objects.all().order_by('order')
    allmotds = []
    for ann in motds:
        allmotds.append(ann.content)
    res = {"telops": {
    "telop": allmotds, 
    "length": len(allmotds)}}
    return JsonResponse(res)

@csrf_exempt
def language(request, region):
    lang = request.GET.get('lang', None)
    if lang == None:
        return JsonResponse({"error": True})
    res = {"languages":{"language":[{
    "iso_code":lang,
    "name":"Unknown"}]}}
    return JsonResponse(res)

#Message de bienvenue (Terms of Service)
#this should be named just tos but nintendo named it eshop message idfk why
@csrf_exempt
def eshop_message(request, region):
    res = {"text": {"type": "html", "body": settings.TOS_ESHOP}}
    return JsonResponse(res)

#
@csrf_exempt
def directories(request, region):
    dirs = category.objects.all().order_by('order')
    alldirectories = []
    for directory in dirs:
        alldirectories.append({
            "name": directory.name, 
            "icon_url": directory.icon_url, 
            "icon_width": 128, 
            "icon_height": 96, 
            "banner_url": directory.banner_url, 
            "index": directory.index, 
            "id": directory.id, 
            "type": "search", 
            "standard": directory.standard, 
            "new": directory.new})
    res = {"directories": 
    {"directory": alldirectories, 
    "length": len(alldirectories), 
    "catalog_id": 1}}
    return JsonResponse(res)

#
@csrf_exempt
def directory(request, region, cid):
    try:
        dir = category.objects.get(id=cid)
    except ObjectDoesNotExist:
        return JsonResponse({"error": True})
    if request.GET.get("platform[]") == None and request.GET.get("genre[]") == None and request.GET.get("publisher[]") == None and request.GET.get("price_max")==None and request.GET.get("price_min")==None:
        titles = Title.objects.filter(category=dir, public=True).order_by('-date')[int(request.GET.get("offset")):25+25]
        total = titles.count()
        movies = movie.objects.filter(category=dir).order_by('-date')
        total_movie = movies.count()
        total = total+total_movie
    else:
        #over complicated but at least works
        if request.GET.get("platform[]") == None:
            platforms = []
            all_platforms = platform.objects.all()
            for aplatform in all_platforms:
                platforms.append(aplatform.id)
        else:
            platforms = request.GET.get("platform[]").split(",")
        if request.GET.get("genre[]") == None:
            genrel = []
            all_genre = genre.objects.all()
            for agenre in all_genre:
                genrel.append(agenre.id)
        else:
            genrel = request.GET.get("genre[]").split(",")
        if request.GET.get("publisher[]") == None:
            publisherl = []
            all_publisher = publisher.objects.all()
            for apublisher in all_publisher:
                publisherl.append(apublisher.id)
        else:
            publisherl = request.GET.get("publisher[]").split(",")
        if request.GET.get("price_max") != None and request.GET.get("price_min") == None:
            titles = Title.objects.filter(price__lte=int(request.GET.get("price_max")),category=dir, platform__in=platforms, genre__in=genrel, publisher__in=publisherl, public=True).order_by("-date")[int(request.GET.get("offset")):25+25]
        if request.GET.get("price_min") != None and request.GET.get("price_max") == None:
            titles = Title.objects.filter(price__gte=int(request.GET.get("price_min")),category=dir, platform__in=platforms, genre__in=genrel, publisher__in=publisherl, public=True).order_by("-date")[int(request.GET.get("offset")):25+25]
        if request.GET.get("price_min") != None and request.GET.get("price_max") == None:
            titles = Title.objects.filter(price__gte=int(request.GET.get("price_min")),price__lte=int(request.GET.get("price_max")),category=dir, platform__in=platforms, genre__in=genrel, publisher__in=publisherl, public=True).order_by("-date")[int(request.GET.get("offset")):25+25]
        if request.GET.get("price_max") == None and request.GET.get("price_min")==None:
            titles = Title.objects.filter(category=dir, platform__in=platforms, genre__in=genrel, publisher__in=publisherl, public=True).order_by("-date")[int(request.GET.get("offset")):25+25]
        total = titles.count()
    alltitles = []
    i = 0
    for title in titles:
        if title.is_not_downloadable:
            is_downloadable = False
        else:
            is_downloadable = True
        if title.demo != None:
            demo = True
        else:
            demo = False
        # Préparation des données de la plateforme pour chaque titre
        if title.platform:  # Vérifie si title a une platform associée
            platform_data = {
                "name": title.platform.name, 
                "id": title.platform.id, 
                "device": "CTR"  # Assumant que "CTR" est une valeur fixe ou attribut de platform
            }
        else:
            platform_data = {}  # Ou définir une valeur par défaut appropriée
        
        alltitles.append({"title": {
            "platform": platform_data,  # Utiliser platform_data ici
            "publisher": {
                "name": title.publisher.publisher_name, 
                "id": title.publisher.id}, 
            "publisher": {"name": title.publisher.publisher_name, 
            "id": title.publisher.id}, 
            "display_genre": title.genre.name, 
            "rating_info": {
            "rating_system": {
            "name": title.parentalControl.parental_system_name,
            "id": title.parentalControl.parental_system_id},
            "rating": {
            "icons": {"icon": [{
            "url": title.parentalControl.icon_url_normal, "type": "normal"}, {
            "url": title.parentalControl.icon_url_small, "type": "small"}]},
            "name": title.parentalControl.age_name,
            "age": title.parentalControl.age_number,
            "id": title.parentalControl.id}},
            "star_rating_info": {
            "score": title.rating_score, 
            "votes": title.number_of_votes, 
            "star1": title.number_of_star1, 
            "star2": title.number_of_star2, 
            "star3": title.number_of_star3, 
            "star4": title.number_of_star4, 
            "star5": title.number_of_star5},
            "release_date_on_eshop": str(title.date), 
            "retail_sales": False, 
            "eshop_sales": is_downloadable, 
            "demo_available": demo, 
            "aoc_available": False, 
            "in_app_purchase": title.in_app_purchase, 
            "release_date_on_original": str(title.date), 
            "name": "• "+title.region.initial+" • "+"\n"+title.name, 
            "id": title.id, 
            "product_code": title.product_code, 
            "icon_url": title.icon_url, 
            "banner_url": title.banner_url, 
            "new": title.new}, "index": i})
        i = i + 1
    try:
        for Movie in movies:
            if i > 25:
                continue
            if Movie.is_3d:
                dimension = "3d"
            else:
                dimension = "2d"
            alltitles.append({
                "movie": {
                "name": Movie.name, 
                "banner_url": Movie.banner_url, 
                "thumbnail_url": Movie.thumbnail_url, 
                "files": {"file": [{
                "format": "moflex", 
                "movie_url": Movie.moflex_url, 
                "width": 400, "height": 200, 
                "dimension": dimension, 
                "play_time_sec": Movie.time_in_sec}]}, 
                "id": Movie.id, 
                "new": Movie.new}, "index": i})
            i = i + 1
    except:
        pass
    res = {"directory": {
    "name": dir.name, 
    "icon_url": dir.icon_url, 
    "icon_width": 128, "icon_height": 96, 
    "banner_url": dir.banner_url, 
    "contents": {
    "content": alltitles, 
    "length": len(alltitles), 
    "offset": int(request.GET.get("offset")), 
    "total": total}, 
    "id": dir.id, 
    "type": "search", 
    "component": "title"}}
    return JsonResponse(res)

#Fiche complète d'un jeu    
@csrf_exempt
def title(request, region, tid):
    try:
        title = Title.objects.get(id=tid, public=True)
    except ObjectDoesNotExist:
        return JsonResponse({"error": {"code": "5668", "message": "Le jeu n'existe pas."}})
    title.desc = title.desc.replace("\n", "\n<br>")
    if title.is_not_downloadable:
        is_downloadable = False
    else:
        is_downloadable = True
    if title.demo != None:
        demo = True
    else:
        demo = False
    thumbnails = []
    for url in title.thumbnail_url.split(r" \ "):
        thumbnail = {
            "url": url,
            "height": 112,
            "width": 112,
            "type": "small"
        }
        thumbnails.append(thumbnail)
    
    # Séparation des URLs pour les screenshots
    upper_urls = title.screenshot_upper_url.split(" \ ")
    lower_urls = title.screenshot_lower_url.split(" \ ")
    
    # Vérifiez que les deux listes ont la même longueur
    if len(upper_urls) != len(lower_urls):
        # Gérer l'erreur ou ajuster les listes en conséquence
        pass
    
    screenshots = []
    for i in range(len(upper_urls)):
        screenshot = {
            "image_url": [
                {
                    "value": upper_urls[i].strip(),  # Assurez-vous d'enlever les espaces superflus
                    "type": "upper"
                },
                {
                    "value": lower_urls[i].strip(),  # Assurez-vous d'enlever les espaces superflus
                    "type": "lower"
                }
            ]
        }
        screenshots.append(screenshot)

    genres_data = [{"name": genre.name, "id": genre.id} for genre in title.genre.all()]
    languages_data = [{"iso_code": language.iso_code, "name": language.name} for language in title.language.all()]
    features_data = [{"id": feature.id, "name": feature.name} for feature in title.feature.all()]
    if title.platform:  # Vérifie si title a une platform associée
        platform_data = {
            "name": title.platform.name, 
            "id": title.platform.id, 
            "device": "CTR"  # Assumant que "CTR" est une valeur fixe ou attribut de platform
        }

    res = {"title": {
            "formal_name": title.name,
            "description": title.desc+"\n\n\n"+"Other Informations:"+"\n"+"Region: "+str(title.region.region)+"\n"+"Title ID: "+str(title.tid)+"\n"+"Product Code: "+str(title.product_code)+"\n"+"Version: "+str(title.version)+"\n"+"ID: "+str(title.id),
            "disclaimer": title.disclaimer,
            "genres": {"genre": genres_data, "length": len(genres_data)},
            "languages": {"language": languages_data, "length": len(languages_data)},
            "number_of_players": title.number_of_players,
            "web_sites": {"web_site": [{"name": title.webSite.webSite_name, "url": title.webSite.url, "official": title.webSite.official}], "length": 1},
            "copyright": {"text": title.copyright},
            "keywords": {"keyword": title.keyword.name},
            "features": {"feature": features_data, "length": len(features_data)},
            "ticket_available": title.ticket_available,
            "title_size": title.size,
            "download_code_sales": False,
            "download_card_sales": {"available": False},
            "name": "• "+title.region.initial+" • "+"\n"+title.name, 
            "thumbnails": {"thumbnail": thumbnails},
            "id": title.id,
            "platform": platform_data,
            "publisher": {"name": title.publisher.publisher_name, "id": title.publisher.id},
            "product_code": title.product_code,
            "icon_url": title.icon_url,
            "banner_url": title.banner_url,
            "display_genre": title.genre.name,
            "preference": {"target_player": {"everyone": title.target_player_everyone, "gamers": title.target_player_gamers}, "play_style": {"casual": title.play_style_casual, "intense": title.play_style_intense}},
            "rating_info": {
            "rating_system": {
            "name": title.parentalControl.parental_system_name,
            "id": title.parentalControl.parental_system_id},
            "rating": {
            "icons": {"icon": [{
            "url": title.parentalControl.icon_url_normal, "type": "normal"}, {
            "url": title.parentalControl.icon_url_small, "type": "small"}]},
            "name": title.parentalControl.age_name,
            "age": title.parentalControl.age_number,
            "id": title.parentalControl.id},
            "descriptor": {"descriptor": [{"name": title.descriptor.name}], "length": 1}},
            "star_rating_info": {
            "score": title.rating_score, 
            "votes": title.number_of_votes, 
            "star1": title.number_of_star1, 
            "star2": title.number_of_star2, 
            "star3": title.number_of_star3, 
            "star4": title.number_of_star4, 
            "star5": title.number_of_star5},
            "release_date_on_eshop": str(title.date),
            "retail_sales": False,
            "eshop_sales": is_downloadable,
            "web_sales": is_downloadable,
            "demo_available": demo,
            "aoc_available": False,
            "in_app_purchase": title.in_app_purchase,
            "top_image": {"type": "screenshot", "url": title.top_image_url},
            "new": title.new, 
            "public": title.public,
            "screenshots": {"screenshot": screenshots},
        }
    }
    if demo:
        res["title"]["demo_titles"] = {"demo_title": [{"name": title.demo.name, "id": title.demo.id, "icon_url": title.demo.icon_url}]}
    return JsonResponse(res)

#
@csrf_exempt
def agreement_send_info(request, region):
   return JsonResponse({
    "text":{
    "type":"html",
    "body":"This is useless shit that could break your\naccess to Let's Shop! in the future\ndon't accept plz"}})

#Rechercher par 'Catégorie'
@csrf_exempt
def searchcategory(request, region):
    all_category = searchCategory.objects.all().order_by("-id")
    categories = []
    for category in all_category:
        categories.append({
            "name": category.name, 
            "params": {
            "param": [{
            "key": 
            "platform[]", 
            "value": category.platform_list}]}, 
            "id": category.id})
    res = {"search_categories":{
    "search_category_group":[{
    "name":"Search categories",
    "search_category":categories}]}}
    return JsonResponse(res)

#Rechercher par 'Genres'
@csrf_exempt
def genres(request, region):
    all_genres = genre.objects.all().order_by("-id")
    genres = []
    for agenre in all_genres:
        genres.append({
            "name": agenre.name, 
            "id": agenre.id})
    res = {"genres": {"genre": genres}}
    return JsonResponse(res)

#Rechercher par 'Publisher'
@csrf_exempt
def publishers(request, region):
    all_publishers = publisher.objects.all().order_by("-id")
    publishers = []
    for apublisher in all_publishers:
        publishers.append({
            "name": apublisher.publisher_name, 
            "id": apublisher.id})
    res = {"publishers": {"publisher": publishers}}
    return JsonResponse(res)

#
@csrf_exempt
def contents(request, region):
    search_term = unquote(request.GET.get("freeword"))
    all_titles = Title.objects.filter(name__icontains=search_term, public=True).order_by("-date")[int(request.GET.get("offset")):25+25]
    total = all_titles.count()
    movies = movie.objects.filter(name__icontains=search_term).order_by('-date')
    total_movie = movies.count()
    ##total = total+total_movie
    titles = []
    i = 0
    for title in all_titles:
        if title.is_not_downloadable:
            is_downloadable = False
        else:
            is_downloadable = True
        if title.demo != None:
            demo = True
        else:
            demo = False
        
        # Préparation des données de la plateforme pour chaque titre
        if title.platform:  # Vérifie si title a une platform associée
            platform_data = {
                "name": title.platform.name, 
                "id": title.platform.id, 
                "device": "CTR"  # Assumant que "CTR" est une valeur fixe ou attribut de platform
            }
        else:
            platform_data = {}  # Ou définir une valeur par défaut appropriée
        
        titles.append({"title": {
            "platform": platform_data,  # Utiliser platform_data ici
            "publisher": {
                "name": title.publisher.publisher_name, 
                "id": title.publisher.id}, 
            "display_genre": title.genre.name,
            "star_rating_info": {
            "score": title.rating_score, 
            "votes": title.number_of_votes, 
            "star1": title.number_of_star1, 
            "star2": title.number_of_star2, 
            "star3": title.number_of_star3, 
            "star4": title.number_of_star4, 
            "star5": title.number_of_star5}, 
            "rating_info": {
            "rating_system": {
            "name": title.parentalControl.parental_system_name,
            "id": title.parentalControl.parental_system_id},
            "rating": {
            "icons": {"icon": [{
            "url": title.parentalControl.icon_url_normal, "type": "normal"}, {
            "url": title.parentalControl.icon_url_small, "type": "small"}]},
            "name": title.parentalControl.age_name,
            "age": title.parentalControl.age_number,
            "id": title.parentalControl.id}},
            "release_date_on_eshop": str(title.date), 
            "retail_sales": False, 
            "eshop_sales": is_downloadable, 
            "demo_available": demo, 
            "aoc_available": False, 
            "in_app_purchase": title.in_app_purchase, 
            "release_date_on_original": str(title.date), 
            "name": "• "+title.region.initial+" • "+"\n"+title.name, 
            "id": title.id, 
            "product_code": title.product_code, 
            "icon_url": title.icon_url, 
            "banner_url": title.banner_url, 
            "new": title.new}, 
            "index": i})
        i = i + 1
    for Movie in movies:
        if i > 25:
            continue
        if Movie.is_3d:
            dimension = "3d"
        else:
            dimension = "2d"
        titles.append({"movie": {
            "name": Movie.name, 
            "banner_url": Movie.banner_url, 
            "thumbnail_url": Movie.thumbnail_url, 
            "files": {"file": [{
            "format": "moflex", 
            "movie_url": Movie.moflex_url, 
            "width": 400, "height": 200, 
            "dimension": dimension, 
            "play_time_sec": Movie.time_in_sec}]}, 
            "id": Movie.id, 
            "new": Movie.new}, 
            "index": i})
        i = i + 1
    res = {"contents": {
    "content": titles, 
    "length": len(titles), 
    "offset": int(request.GET.get("offset")), 
    "total": total}}
    return JsonResponse(res)

#
@csrf_exempt
def titles(request, region):
    if request.GET.get("platform[]") == None and request.GET.get("genre[]") == None and request.GET.get("publisher[]") == None and request.GET.get("price_max")==None and request.GET.get("price_min")==None and request.GET.get("title[]") == None:
        if request.GET.get("freeword") != None:
            search_term = unquote(request.GET.get("freeword"))
            all_titles = Title.objects.filter(name__icontains=search_term, public=True).order_by("-date")[int(request.GET.get("offset")):25+25]
            if request.GET.get("release_date_after") == None:
                movies = movie.objects.filter(name__icontains=search_term).order_by('-date')
        if request.GET.get('title[]') == None:
            all_titles = Title.objects.filter(public=True).order_by("-date")[int(request.GET.get("offset")):25+25]
            if request.GET.get("release_date_after") == None:
                movies = movie.objects.all().order_by('-date')
        total = all_titles.count()
        if request.GET.get("release_date_after") == None:
            total_movie = movies.count()
            ##total = total+total_movie
    if request.GET.get("platform[]") != None or request.GET.get("genre[]") != None or request.GET.get("publisher[]") != None or request.GET.get("price_max")!=None or request.GET.get("price_min")!=None:
        #over complicated but at least works
        if request.GET.get("platform[]") == None:
            platforms = []
            all_platforms = platform.objects.all()
            for aplatform in all_platforms:
                platforms.append(aplatform.id)
        else:
            platforms = request.GET.get("platform[]").split(",")
        if request.GET.get("genre[]") == None:
            genrel = []
            all_genre = genre.objects.all()
            for agenre in all_genre:
                genrel.append(agenre.id)
        else:
            genrel = request.GET.get("genre[]").split(",")
        if request.GET.get("publisher[]") == None:
            publisherl = []
            all_publisher = publisher.objects.all()
            for apublisher in all_publisher:
                publisherl.append(apublisher.id)
        else:
            publisherl = request.GET.get("publisher[]").split(",")
        if request.GET.get("freeword") != None:
            search_term = unquote(request.GET.get("freeword"))
            if request.GET.get("price_max") != None and request.GET.get("price_min") == None:
                all_titles = Title.objects.filter(price__lte=int(request.GET.get("price_max")), name__icontains=search_term,platform__in=platforms, genre__in=genrel, publisher__in=publisherl, public=True).order_by("-date")[int(request.GET.get("offset")):25+25]
            if request.GET.get("price_min") != None and request.GET.get("price_max") == None:
                all_titles = Title.objects.filter(price__gte=int(request.GET.get("price_min")),name__icontains=search_term,platform__in=platforms, genre__in=genrel, publisher__in=publisherl, public=True).order_by("-date")[int(request.GET.get("offset")):25+25]
            if request.GET.get("price_max") != None and request.GET.get("price_min") != None:
                all_titles = Title.objects.filter(price__lte=int(request.GET.get("price_max")),price__gte=int(request.GET.get("price_min")),name__icontains=search_term,platform__in=platforms, genre__in=genrel, publisher__in=publisherl, public=True).order_by("-date")[int(request.GET.get("offset")):25+25]
            if request.GET.get("price_max") == None and request.GET.get("price_min")==None:
                all_titles = Title.objects.filter(name__icontains=search_term,platform__in=platforms, genre__in=genrel, publisher__in=publisherl, public=True).order_by("-date")[int(request.GET.get("offset")):25+25]
        else:
            if request.GET.get("price_max") != None and request.GET.get("price_min") == None:
                all_titles = Title.objects.filter(price__lte=int(request.GET.get("price_max")), platform__in=platforms, genre__in=genrel, publisher__in=publisherl, public=True).order_by("-date")[int(request.GET.get("offset")):25+25]
            if request.GET.get("price_min") != None and request.GET.get("price_max") == None:
                all_titles = Title.objects.filter(price__gte=int(request.GET.get("price_min")), platform__in=platforms, genre__in=genrel, publisher__in=publisherl, public=True).order_by("-date")[int(request.GET.get("offset")):25+25]
            if request.GET.get("price_max") != None and request.GET.get("price_min") != None:
                all_titles = Title.objects.filter(price__lte=int(request.GET.get("price_max")),price__gte=int(request.GET.get("price_min")),platform__in=platforms, genre__in=genrel, publisher__in=publisherl, public=True).order_by("-date")[int(request.GET.get("offset")):25+25]
            if request.GET.get("price_max") == None and request.GET.get("price_min")==None:
                all_titles = Title.objects.filter(platform__in=platforms, genre__in=genrel, publisher__in=publisherl, public=True).order_by("-date")[int(request.GET.get("offset")):25+25]
        total = all_titles.count()
    if request.GET.get("title[]") != None:
        title_ids = request.GET.get("title[]").split(",")
        all_titles = Title.objects.filter(id__in=title_ids)
        total = all_titles.count()
    titles = []
    i = 0
    for title in all_titles:
        #check date
        if request.GET.get("release_date_after"):
            now = datetime.date.today()
            time_between_insertion = now - title.date
            if int(time_between_insertion.days) > 90:
                continue
        if title.is_not_downloadable:
            is_downloadable = False
        else:
            is_downloadable = True
        if title.demo != None:
            demo = True
        else:
            demo = False
        # Préparation des données de la plateforme pour chaque titre
        if title.platform:  # Vérifie si title a une platform associée
            platform_data = {
                "name": title.platform.name, 
                "id": title.platform.id, 
                "device": "CTR"  # Assumant que "CTR" est une valeur fixe ou attribut de platform
            }
        else:
            platform_data = {}  # Ou définir une valeur par défaut appropriée
        
        titles.append({"title": {
            "platform": platform_data,  # Utiliser platform_data ici
            "publisher": {
                "name": title.publisher.publisher_name, 
                "id": title.publisher.id},  
            "publisher": {
            "name": title.publisher.publisher_name, 
            "id": title.publisher.id}, 
            "display_genre": title.genre.name, 
            "rating_info": {
            "rating_system": {
            "name": title.parentalControl.parental_system_name,
            "id": title.parentalControl.parental_system_id},
            "rating": {
            "icons": {"icon": [{
            "url": title.parentalControl.icon_url_normal, "type": "normal"}, {
            "url": title.parentalControl.icon_url_small, "type": "small"}]},
            "name": title.parentalControl.age_name,
            "age": title.parentalControl.age_number,
            "id": title.parentalControl.id}},
            "star_rating_info": {
            "score": title.rating_score, 
            "votes": title.number_of_votes, 
            "star1": title.number_of_star1, 
            "star2": title.number_of_star2, 
            "star3": title.number_of_star3, 
            "star4": title.number_of_star4, 
            "star5": title.number_of_star5},
            "release_date_on_eshop": str(title.date), 
            "retail_sales": False, 
            "eshop_sales": is_downloadable, 
            "demo_available": demo, 
            "aoc_available": False, 
            "in_app_purchase": title.in_app_purchase, 
            "release_date_on_original": str(title.date), 
            "name": "• "+title.region.initial+" • "+"\n"+title.name, 
            "id": title.id, 
            "product_code": title.product_code, 
            "icon_url": title.icon_url, 
            "banner_url": title.banner_url, 
            "new": title.new}, 
            "index": i})
        i = i + 1
    try:
        for Movie in movies:
            if i > 25:
                continue
            if Movie.is_3d:
                dimension = "3d"
            else:
                dimension = "2d"
            titles.append({"movie": {
                "name": Movie.name, 
                "banner_url": Movie.banner_url, 
                "thumbnail_url": Movie.thumbnail_url, 
                "files": {"file": [{
                "format": "moflex", 
                "movie_url": Movie.moflex_url, 
                "width": 400, "height": 200, 
                "dimension": dimension, 
                "play_time_sec": Movie.time_in_sec}]}, 
                "id": Movie.id, 
                "new": Movie.new}, 
                "index": i})
            i = i + 1
    except:
        pass
    if request.GET.get("offset") == None:
        offset = 0
    else:
        offset = int(request.GET.get("offset"))
    res = {"contents": {
    "content": titles, 
    "length": len(titles), 
    "offset": offset, 
    "total": total}}
    return JsonResponse(res)

#Voir un Moflex (Format de vidéo Nintendo 3DS)
@csrf_exempt
def viewmovie(request, region, mid):
    try:
        Movie = movie.objects.get(id=mid)
    except ObjectDoesNotExist:
        return JsonResponse({"error": True})
    if Movie.is_3d:
        dimension = "3d"
    else:
        dimension = "2d"
    res = {"movie": {
    "name": Movie.name, 
    "banner_url": Movie.banner_url, 
    "thumbnail_url": Movie.thumbnail_url, 
    "files": {"file": [{
    "format": "moflex", 
    "movie_url": Movie.moflex_url, 
    "width": 400, "height": 200, 
    "dimension": dimension, 
    "play_time_sec": Movie.time_in_sec}]}, 
    "id": Movie.id, 
    "new": Movie.new}}
    return JsonResponse(res)

#Fiche d'information des Moflex (Format de vidéo Nintendo 3DS)
@csrf_exempt
def movies_content(request, region):
    movies = movie.objects.all().order_by('-date')[int(request.GET.get("offset")):25+25]
    total = movies.count()
    all_movies = []
    i = 0
    for Movie in movies:
        if request.GET.get("release_date_after"):
            now = datetime.date.today()
            time_between_insertion = now - Movie.date
            if int(time_between_insertion.days) > 7:
                continue
        if Movie.is_3d:
            dimension = "3d"
        else:
            dimension = "2d"
        all_movies.append({"movie": {
            "name": Movie.name, 
            "banner_url": Movie.banner_url, 
            "thumbnail_url": Movie.thumbnail_url, 
            "files": {"file": [{
            "format": "moflex", 
            "movie_url": Movie.moflex_url, 
            "width": 400, "height": 200, 
            "dimension": dimension, 
            "play_time_sec": Movie.time_in_sec}]}, 
            "id": Movie.id, 
            "new": Movie.new}, 
            "index": i})
        i = i + 1
    res = {"contents": {
    "content": all_movies, 
    "length": len(all_movies), 
    "offset": int(request.GET.get("offset")), 
    "total": total}}
    return JsonResponse(res)

#Fonction de Classement
#Until I get the time to implement proper rankings (quite complicated)
@csrf_exempt
def rankings(request, region):
    platforms = platform.objects.all().order_by('-id')
    pf = []
    for aplatform in platforms:
        pf.append({
            "name": aplatform.name, 
            "id": aplatform.id})
    if pf == []:
        res = {"rankings": {
        "ranking": []}, "length": 0}
    else:
        res = {"rankings": {
        "ranking": [{
        "name": "All software", 
        "filters": {"filter": pf}, 
        "type": "title", 
        "id": 1}]}, 
        "length": 1}
    return JsonResponse(res)
#Fonction de Classement
@csrf_exempt
def ranking(request, region, rid):
    return JsonResponse({
        "error": {
        "code": "5654", "message": "Hello ! This function are not available for the moment..."}}, 
        status=400)