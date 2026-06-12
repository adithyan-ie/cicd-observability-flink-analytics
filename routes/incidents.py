from flask import Blueprint, render_template, request, redirect
from flask_login import login_required
from extensions import db
from models.incident import Incident

incident_bp=Blueprint('incident',__name__)

@incident_bp.route('/incidents')
@login_required
def incidents():
    return render_template('incidents.html', incidents=Incident.query.all())

@incident_bp.route('/incidents/create', methods=['GET','POST'])
@login_required
def create_incident():
    if request.method=='POST':
        i=Incident(title=request.form['title'],
                   description=request.form['description'],
                   severity=request.form['severity'])
        db.session.add(i); db.session.commit()
        return redirect('/incidents')
    return render_template('create_incident.html')

@incident_bp.route('/incidents/<int:id>/close')
@login_required
def close_incident(id):
    i=Incident.query.get_or_404(id)
    i.status='Closed'
    db.session.commit()
    return redirect('/incidents')
