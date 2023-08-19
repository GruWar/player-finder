@app.route("/group_info/<int:group_id>")
@login_required
def group_info(group_id):
    requested_group = Group.query.get(group_id)
    return render_template("group_info.html", current_user=current_user, group=requested_group)