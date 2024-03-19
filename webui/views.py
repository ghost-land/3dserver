from django.shortcuts import render
from django.http import HttpResponseRedirect, Http404, HttpResponse
from shopdeckdb.models import *
from django.contrib.auth import authenticate, login, logout
from django.core.validators import EmailValidator
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from shopdeck.settings import WEBUI_NAME
# Create your views here.

print("WebUI Starting Up")

def index(request):
    if not request.user.is_authenticated:
        return render(request, "welcome.html", {"WEBUI_NAME": WEBUI_NAME})
    owned = ownedTitle.objects.filter(owner=request.user.linked_ds)
    titles = []
    for title in owned:
        if title.title.version > title.version:
            titles.append(title)
    updates = len(titles)
    recent = Title.objects.filter(public=True).order_by('-date')[0:9]
    random = Title.objects.filter(public=True).order_by('?')[0:9]
    return render(request, "index.html", {"title": "Home", "WEBUI_NAME": WEBUI_NAME, "user": request.user, "updates": updates, "random": random, "recent": recent})

def all_titles(request):
    sort_option = request.GET.get('sort')

    if sort_option == 'name_asc':
        titles = Title.objects.filter(public=True).order_by('name')
    elif sort_option == 'name_desc':
        titles = Title.objects.filter(public=True).order_by('-name')
    elif sort_option == 'date_asc':
        titles = Title.objects.filter(public=True).order_by('date')
    elif sort_option == 'date_desc':
        titles = Title.objects.filter(public=True).order_by('-date')
    else:
        titles = Title.objects.filter(public=True).order_by('-date')

    return render(request, "all_titles.html", {"titles": titles, "title": "All Titles", "WEBUI_NAME": WEBUI_NAME})

def title(request, tid):
    if not request.user.is_authenticated:
        return HttpResponseRedirect("/login") # Redirect to login page if user is not logged in

    owned = ownedTitle.objects.filter(owner=request.user.linked_ds)
    titles = []
    for title in owned:
        if title.title.version > title.version:
            titles.append(title)
    updates = len(titles)

    try:
        title = Title.objects.get(id=tid, public=True)
    except ObjectDoesNotExist:
        raise Http404()

    try:
        wishlisted = wishlistedTitle.objects.get(title=title, owner=request.user.linked_ds)
        wishlisted = True
    except ObjectDoesNotExist:
        wishlisted = False

    title.desc = title.desc.replace('\n', '<br>')

    # Splitting the screenshot URLs by ' \ ' and removing empty strings
    screenshots = [url.strip() for url in title.screenshot_merged_url.split('\\') if url.strip()]

    return render(request, "title.html", {
        "title": title.name,
        "WEBUI_NAME": WEBUI_NAME,
        "user": request.user,
        "app": title,
        "updates": updates,
        "wishlisted": wishlisted,
        "screenshots": screenshots
    })

def add_wishlist(request):
    id = request.GET.get("id")
    if id==None:
        return HttpResponse("could not parse request")
    try:
        title = Title.objects.get(id=int(id), public=True)
    except ObjectDoesNotExist:
        raise Http404()
    try:
        wishlisted = wishlistedTitle.objects.get(title=title, owner=request.user.linked_ds)
        return HttpResponse("This is already wishlisted; cannot continue! (sorry)")
    except ObjectDoesNotExist:
        pass
    wishlisted = wishlistedTitle.objects.create(title=title, owner=request.user.linked_ds)
    return HttpResponseRedirect('/title/'+id)

def remove_wishlist(request):
    id = request.GET.get("id")
    if id==None:
        return HttpResponse("could not parse request")
    if request.GET.get("redirect")==None:
        return HttpResponse("could not parse request")
    try:
        title = Title.objects.get(id=int(id), public=True)
    except ObjectDoesNotExist:
        raise Http404()
    try:
        wishlisted = wishlistedTitle.objects.get(title=title, owner=request.user.linked_ds)
    except ObjectDoesNotExist:
        return HttpResponse("This is already wishlisted; cannot continue! (sorry)")
    wishlisted.delete()
    return HttpResponseRedirect(request.GET.get('redirect'))

def current_balance(request):
    owned = ownedTitle.objects.filter(owner=request.user.linked_ds)
    titles = []
    for title in owned:
        if title.title.version > title.version:
            titles.append(title)
    updates = len(titles)
    return render(request, "current.html", {"title": "Current balance", "WEBUI_NAME":WEBUI_NAME, "user": request.user,"updates": updates})

def add_balance(request):
    owned = ownedTitle.objects.filter(owner=request.user.linked_ds)
    titles = []
    for title in owned:
        if title.title.version > title.version:
            titles.append(title)
    updates = len(titles)
    card = request.GET.get("card")
    if card==None:
        return render(request, "_error.html", {"title": "Error", "WEBUI_NAME":WEBUI_NAME, "user": request.user,"updates": updates, "message": "No code was found."})
    try:
        card = redeemableCard.objects.get(code=card)
    except ObjectDoesNotExist:
        return render(request, "_error.html", {"title": "Error", "WEBUI_NAME":WEBUI_NAME, "user": request.user,"updates": updates, "message": "This code is invalid. Please recheck it and try again."})
    if card.used:
        return render(request, "_error.html", {"title": "Error", "WEBUI_NAME":WEBUI_NAME, "user": request.user,"updates": updates, "message": "This card has already been used."})
    if not card.is_money:
        return render(request, "_error.html", {"title": "Error", "WEBUI_NAME":WEBUI_NAME, "user": request.user,"updates": updates, "message": "This card does not contains money, but an application. Redeem it on a 3DS."})
    if request.GET.get("go") == None:
        return render(request, "add.html", {"title": "Add balance", "WEBUI_NAME":WEBUI_NAME, "user": request.user,"updates": updates, "code": request.GET.get("card"), "card": card})
    else:
        ds = request.user.linked_ds
        newamount = ds.balance + int(card.content)
        ds.balance = ds.balance + int(card.content)
        ds.save()
        card.used = True
        card.save()
        return render(request, "success.html", {"title": "Add balance", "WEBUI_NAME":WEBUI_NAME, "user": request.user,"updates": updates, "newamount": newamount, "card": card})

def wishlist(request):
    wishlisted = wishlistedTitle.objects.filter(owner=request.user.linked_ds).order_by("-id")
    owned = ownedTitle.objects.filter(owner=request.user.linked_ds)
    titles = []
    for title in owned:
        if title.title.version > title.version:
            titles.append(title)
    updates = len(titles)
    return render(request, "wishlist.html", {"title": "Wishlist", "WEBUI_NAME":WEBUI_NAME, "user": request.user,"updates": updates, "wishlist": wishlisted, "wishlistedpage": "yes"})
    

def connect(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect("/")
    if request.method == 'POST':
        if request.POST.get('username') == "" or request.POST.get('password') == "": 
            return render(request, "login.html", {"vh": 100, "title": "Login", "message": "All fields weren't filled.", "WEBUI_NAME": WEBUI_NAME})
        else:
            user = authenticate(username=request.POST.get("username"), password=request.POST.get("password"))
            if user == None:
                return render(request, "login.html", {"vh": 100, "title": "Login", "message": "The username/password is incorrect.", "WEBUI_NAME": WEBUI_NAME})
            else:
                login(request, user)
                return HttpResponseRedirect("/")
    return render(request, 'login.html', {"vh": 100, "title": "Login", "WEBUI_NAME": WEBUI_NAME})

def disconnect(request):
    if request.user.is_authenticated:
        logout(request)
        return HttpResponseRedirect("/")
    else:
        return HttpResponseRedirect("/")
            
def register(request):
    if request.user.is_authenticated:
        return HttpResponseRedirect("/")
    if request.method == 'POST':
        if request.POST.get('username') == "" or request.POST.get('password') == "" or request.POST.get('passwordconfirm') == "" or request.POST.get('email') == "" or request.POST.get('3dskey') == "": 
            return render(request, "signup.html", {"vh": 105, "title": "Sign Up", "message": "All fields weren't filled.", "WEBUI_NAME": WEBUI_NAME})
        else:
            if request.POST.get("password") != request.POST.get("passwordconfirm"):
                return render(request, "signup.html", {"vh": 105, "title": "Sign Up", "message": "Passwords don't match.", "WEBUI_NAME": WEBUI_NAME})
            try:
                EmailValidator()(value=request.POST.get("email"))
            except ValidationError:
                return render(request, "signup.html", {"vh": 105, "title": "Sign Up", "message": "Email is not valid.", "WEBUI_NAME": WEBUI_NAME})
            try:
                conflict = User.objects.get(username=request.POST.get("username"))
                return render(request, "signup.html", {"vh": 105, "title": "Sign Up", "message": "A user with the same username already exists.", "WEBUI_NAME": WEBUI_NAME})
            except ObjectDoesNotExist:
                pass
            try:
                ds = Client3DS.objects.get(uniquekey=request.POST.get("3dskey"))
                try:
                    conflict = User.objects.get(linked_ds=ds)
                    return render(request, "signup.html", {"vh": 105, "title": "Sign Up", "message": "An account is already linked with this 3DS.", "WEBUI_NAME": WEBUI_NAME})
                except ObjectDoesNotExist:
                    pass
                user = User.objects.create_user(request.POST.get("username"), request.POST.get("email"), request.POST.get("password"))
                user.linked_ds = ds
                user.save()
                return HttpResponseRedirect("/login")
            except ObjectDoesNotExist:
                return render(request, "signup.html", {"vh": 105, "title": "Sign Up", "message": "A 3DS corresponding to your 3DS Key was not found.", "WEBUI_NAME": WEBUI_NAME})
    return render(request, "signup.html", {"vh": 105, "title": "Sign Up", "WEBUI_NAME": WEBUI_NAME})

def downloaded(request):
    owned = ownedTitle.objects.filter(owner=request.user.linked_ds).order_by("-id")
    titles = []
    for title in owned:
        if title.title.version > title.version:
            titles.append(title)
    updates = len(titles)
    return render(request, "downloaded.html", {"title": "Downloaded titles & updates", "WEBUI_NAME":WEBUI_NAME, "user": request.user,"updates": updates, "downloaded": owned, "titles": titles})

def search(request):
    owned = ownedTitle.objects.filter(owner=request.user.linked_ds).order_by("-id")
    titles = []
    for title in owned:
        if title.title.version > title.version:
            titles.append(title)
    updates = len(titles)
    
    if request.method == "GET":
        title_name = request.GET.get("title_name")
        tid = request.GET.get("tid")
        product_code = request.GET.get("product_code")
        
        if not title_name and not tid and not product_code:
            return render(request, "search.html", {"title": "Search", "WEBUI_NAME":WEBUI_NAME, "user": request.user,"updates": updates})
        
        if (title_name and tid) or (title_name and product_code) or (tid and product_code):
            return render(request, "_error.html", {"title": "Error", "WEBUI_NAME":WEBUI_NAME, "user": request.user,"updates": updates, "message": "Please fill in only one search field."})
        
        if title_name:
            # Search by title name
            searched = Title.objects.filter(name__icontains=title_name, public=True).order_by('-date')
        elif tid:
            # Search by TID
            searched = Title.objects.filter(tid__icontains=tid, public=True).order_by('-date')
        elif product_code:
            # Search by product code
            searched = Title.objects.filter(product_code__icontains=product_code, public=True).order_by('-date')

        return render(request, "searchresult.html", {"title": "Search Results", "WEBUI_NAME": WEBUI_NAME, "user": request.user, "updates": updates, "results": searched})

def random_title(request):
    random_title = Title.objects.filter(public=True).order_by('?').first()
    if random_title is None:
        return HttpResponse("No titles available.")
    else:
        return HttpResponseRedirect('/title/' + str(random_title.id))

def err404(request, exception):
    return render(request, "404.html")

def err500(request):
    return render(request, "500.html")
