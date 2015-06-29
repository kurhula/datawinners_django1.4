function(doc) {
    if (doc.document_type == 'FormModel' && !doc.is_registration_model && doc.form_code != 'delete') {
        if(!doc.void && !doc.xform){
            emit(doc.name.toLowerCase(), {"id":doc._id, "name":doc.name, "is_poll": doc.is_poll});
        }
    }
}

