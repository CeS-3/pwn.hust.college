from urllib.parse import quote

from flask import request, Blueprint, render_template
from CTFd.utils.user import get_current_user, is_admin
from CTFd.utils.decorators import authed_only, admins_only
from CTFd.plugins import bypass_csrf_protection

from ..utils import redirect_internal
from ..utils.dojo import get_current_dojo_challenge


sensai = Blueprint("pwncollege_sensai", __name__)


@sensai.route("/sensai")
@authed_only
def view_sensai():
    active = bool(get_current_dojo_challenge())
    return render_template("iframe.html", iframe_name="sensai", iframe_src="/sensai/", active=active)


@sensai.route("/sensai/", methods=["GET", "POST"])
@sensai.route("/sensai/<path:path>", methods=["GET", "POST"])
@sensai.route("/sensai/", websocket=True)
@sensai.route("/sensai/<path:path>", websocket=True)
@authed_only
@bypass_csrf_protection
def forward_sensai(path=""):
    query_string = request.query_string.decode('utf-8')
    full_path = f"{path}?{query_string}" if query_string else path
    user = get_current_user()
    user_type = "User" if not is_admin() else "Admin"
    return redirect_internal(f"http://sensai:8080/{full_path}", auth=f"{user_type};{user.id};{user.name};{user.email};{user.password}")
