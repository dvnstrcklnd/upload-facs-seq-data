import csv

def jobs_for(operation_type_name, trace):
    return [j for j in trace.get_jobs() if j.operation_type.name == operation_type_name]
            
def get_backtrace(job_id, aq_session):
    return aq_session.Job.find(job_id).state

def get_item_ids(args, nav):
    aq_instance = nav.aq_instance
    if args.item_ids:
        item_ids = args.item_ids
        item_ids = [int(i) for i in sorted(list(set(item_ids)))]
        msg = "Finding metadata for Items {} on {}"
        print(msg.format(item_ids, aq_instance) + "\n")

    elif args.plan_id:
        plan_id = int(args.plan_id)
        operation_type = args.operation_type or "Dilute to 4nM"
        output_name = args.output_name or "DNA library out"
        item_ids = nav.plan_outputs(plan_id, operation_type, output_name)
        msg = "Finding metadata for {} outputs to {} in Plan {} on {}"
        print(msg.format(output_name, operation_type, plan_id, aq_instance) + "\n")

    else:
        raise "You must provide either Item IDs or a Plan ID."

    return item_ids
    
def get_ops_by_name(ops, name):
    return [o for o in ops if o.operation_type.name == name]

def get_batch_data(nav, known_item_ids):
    batch_data = {}

    for item_ids in known_item_ids:
        # Test whether item_ids is iterable or a single id
        # Iterables are more forgiving of broken provenance
        try:
            first_known_item_id = item_ids[0]
            last_known_item_id = item_ids[-1]
        except TypeError:
            first_known_item_id = item_ids
            last_known_item_id = item_ids

        found_ops = nav.walk_back('Challenge and Label', first_known_item_id)

        subs = (found_ops[-1].operation_type.name, str(item_ids))
        print("Terminated at Operation \"%s\" for Item %s" % subs)

        cl_ops = get_ops_by_name(found_ops, 'Challenge and Label')
        st_ops = get_ops_by_name(found_ops, 'Sort Yeast Display Library')
        ic_ops = get_ops_by_name(found_ops, 'Innoculate Yeast Library')
        if not ic_ops:
            ic_ops = get_ops_by_name(found_ops, 'Mix Cultures')


        bc_ops = get_ops_by_name(found_ops, ['Make qPCR Fragment', 'Make qPCR Fragment WITH PLATES'])
        bc_ops = [op for op in bc_ops if op.input("Program").value == "qPCR2"]

        data = {}
        if len(cl_ops) == 1 and len(st_ops) == 1:
            data['cl_op'] = cl_ops[0]
            data['st_op'] = st_ops[0]

            st_jas = nav.session.JobAssociation.where({'operation_id': data['st_op'].id})
            st_job_id = st_jas[-1].job_id # Find the last Job in case of restart
            data['st_job_id'] = st_job_id

        elif len(ic_ops) == 1:
            data['ic_op'] = ic_ops[0]

        else:
            msg = "Unexpected operation history for Item %d: %s"
            history = str([op.operation_type.name for op in found_ops])
            # raise Exception(msg % (last_known_item_id, history))
            print(msg % (last_known_item_id, history))

        if bc_ops:
            data['bc_op'] = bc_ops[0]

        batch_data[last_known_item_id] = data
        print("")

    return batch_data

def library_associations(chal_op, sort_op):
    item = chal_op.input('Yeast Culture').item

    if not item:
        return {}

    associations = {'item_id': item.id, 'round_id': 'Specimen_001'}

    update_associations(item, associations)
    update_associations(chal_op.output('Labeled Yeast Library').item, associations)
    update_associations(sort_op.output('Labeled Yeast Library').item, associations)

    return associations

def update_associations(item, associations):
    if item:
        for a in item.data_associations:
            associations.update(a.object)

def facs_filename(associations):
    fn = "" #associations['round_id'] + "_"
    st_id = associations.get('software_tube_id', '')

    if isinstance(st_id, str):
        return fn + st_id
    elif isinstance(st_id, list):
        return ", ".join([fn + s for s in st_id])

def collect_data(nav, item_ids):
    all_data = {}
    ngs_sample_data = get_batch_data(nav, item_ids)
    all_data.update(ngs_sample_data)

    ngs_st_op_ids = [d['st_op'].id for d in ngs_sample_data.values() if d.get('st_op')]

    st_job_ids = [d['st_job_id'] for d in ngs_sample_data.values() if d.get('st_job_id')]
    st_job_ids = list(set(st_job_ids))
    st_jobs = nav.session.Job.find(st_job_ids) or []

    sort_only_item_ids = []
    for job in st_jobs:
        for op in job.operations:
            if not op.id in ngs_st_op_ids:
                out_id = op.output('Labeled Yeast Library').item.id
                sort_only_item_ids.append(out_id)

    other_sample_data = get_batch_data(nav, sort_only_item_ids)
    all_data.update(other_sample_data)
    return all_data

def write_to_csv(all_data, nav):
    csv_headers = [
        'aq_item_id',
        'strain',
        'protease',
        'concentration',
        'sort_job',
        'facs_filename_stub',
        'frac_positive',
        'sort_count'
    ]

    csv_rows = []

    for last_known_item_id, data in all_data.items():
        row = {}
        row['aq_item_id'] = str(last_known_item_id)

        if data.get('cl_op') and data.get('st_op'):
            associations = library_associations(data.get('cl_op'), data.get('st_op'))

            cl_op = data.get('cl_op')
            row['strain'] = cl_op.input('Yeast Culture').sample.name
            row['protease'] = cl_op.input('Protease').sample.name
            row['concentration'] = str(cl_op.field_value('Protease Concentration', 'input').value)

            row['sort_job'] = "Job_%d" % data.get('st_job_id')
            row['facs_filename_stub'] = facs_filename(associations)
            row['frac_positive'] = str(associations.get('frac_positive', ''))
            row['sort_count'] = str(associations.get('sort_count', ''))

        elif data.get('ic_op'):
            last_known_item = nav.session.Item.find(last_known_item_id)
            row['strain'] = last_known_item.sample.name
            row['protease'] = 'naive'

        csv_rows.append(row)

    with open('staging/manifest.csv', 'w', newline='') as csvfile:
        cw = csv.DictWriter(csvfile, csv_headers)
        cw.writeheader()

        for row in csv_rows:
            cw.writerow(row)

# def get_challenge_metadata(chal_op):
#     challenge_metadata = {}
#     prot_name = chal_op.input('Protease').sample.name
#     prot_conc = str(chal_op.field_value('Protease Concentration', 'input').value)

#     challenge_metadata['strain'] = chal_op.input('Yeast Culture').sample.name
#     challenge_metadata['protease'] = prot_name.lower()
#     challenge_metadata['concentration'] = prot_conc

#     return challenge_metadata