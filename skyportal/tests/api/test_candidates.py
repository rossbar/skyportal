import datetime
import numpy.testing as npt
import uuid

from skyportal.tests import api

from tdtax import taxonomy, __version__


def test_candidate_list(view_only_token, public_candidate):
    status, data = api("GET", "candidates", token=view_only_token)
    assert status == 200
    assert data["status"] == "success"


def test_candidate_existence(view_only_token, public_candidate):
    status, _ = api('HEAD', f'candidates/{public_candidate.id}', token=view_only_token)
    assert status == 200

    status, _ = api(
        'HEAD', f'candidates/{public_candidate.id[:-1]}', token=view_only_token
    )
    assert status == 404


def test_token_user_retrieving_candidate(view_only_token, public_candidate):
    status, data = api(
        "GET", f"candidates/{public_candidate.id}", token=view_only_token
    )
    assert status == 200
    assert data["status"] == "success"
    assert all(k in data["data"] for k in ["ra", "dec", "redshift", "dm"])
    assert "photometry" not in data["data"]


def test_token_user_retrieving_candidate_with_phot(view_only_token, public_candidate):
    status, data = api(
        "GET",
        f"candidates/{public_candidate.id}?includePhotometry=true",
        token=view_only_token,
    )
    assert status == 200
    assert data["status"] == "success"
    assert all(k in data["data"] for k in ["ra", "dec", "redshift", "dm", "photometry"])


def test_token_user_retrieving_candidate_with_spec(view_only_token, public_candidate):
    status, data = api(
        "GET",
        f"candidates/{public_candidate.id}?includeSpectra=true",
        token=view_only_token,
    )
    assert status == 200
    assert data["status"] == "success"
    assert all(k in data["data"] for k in ["ra", "dec", "redshift", "dm", "spectra"])


def test_token_user_post_delete_new_candidate(
    upload_data_token, view_only_token, public_filter,
):
    obj_id = str(uuid.uuid4())
    status, data = api(
        "POST",
        "candidates",
        data={
            "id": obj_id,
            "ra": 234.22,
            "dec": -22.33,
            "redshift": 3,
            "transient": False,
            "ra_dis": 2.3,
            "filter_ids": [public_filter.id],
            "passed_at": str(datetime.datetime.utcnow()),
        },
        token=upload_data_token,
    )
    assert status == 200
    candidate_id = data["data"]["ids"][0]

    status, data = api("GET", f"candidates/{obj_id}", token=view_only_token)
    assert status == 200
    assert data["data"]["id"] == obj_id
    npt.assert_almost_equal(data["data"]["ra"], 234.22)

    status, data = api("DELETE", f"candidates/{candidate_id}", token=upload_data_token,)
    assert status == 200


def test_cannot_add_candidate_without_filter_id(upload_data_token):
    obj_id = str(uuid.uuid4())
    status, data = api(
        "POST",
        "candidates",
        data={
            "id": obj_id,
            "ra": 234.22,
            "dec": -22.33,
            "redshift": 3,
            "transient": False,
            "ra_dis": 2.3,
            "passed_at": str(datetime.datetime.utcnow()),
        },
        token=upload_data_token,
    )
    assert status == 400


def test_cannot_add_candidate_without_passed_at(upload_data_token, public_filter):
    obj_id = str(uuid.uuid4())
    status, data = api(
        "POST",
        "candidates",
        data={
            "id": obj_id,
            "ra": 234.22,
            "dec": -22.33,
            "redshift": 3,
            "transient": False,
            "ra_dis": 2.3,
            "filter_ids": [public_filter.id],
        },
        token=upload_data_token,
    )
    assert status == 400


def test_token_user_post_two_candidates_same_obj_filter(
    upload_data_token, view_only_token, public_filter
):
    obj_id = str(uuid.uuid4())
    status, data = api(
        "POST",
        "candidates",
        data={
            "id": obj_id,
            "ra": 234.22,
            "dec": -22.33,
            "redshift": 3,
            "transient": False,
            "ra_dis": 2.3,
            "filter_ids": [public_filter.id],
            "passed_at": str(datetime.datetime.utcnow()),
        },
        token=upload_data_token,
    )
    assert status == 200

    status, data = api("GET", f"candidates/{obj_id}", token=view_only_token)
    assert status == 200
    assert data["data"]["id"] == obj_id
    npt.assert_almost_equal(data["data"]["ra"], 234.22)

    status, data = api(
        "POST",
        "candidates",
        data={
            "id": obj_id,
            "ra": 234.22,
            "dec": -22.33,
            "redshift": 3,
            "transient": False,
            "ra_dis": 2.3,
            "filter_ids": [public_filter.id],
            "passed_at": str(datetime.datetime.utcnow()),
        },
        token=upload_data_token,
    )
    assert status == 200


def test_token_user_cannot_post_two_candidates_same_obj_filter_passed_at(
    upload_data_token, view_only_token, public_filter
):
    obj_id = str(uuid.uuid4())
    passed_at = str(datetime.datetime.utcnow())
    status, data = api(
        "POST",
        "candidates",
        data={
            "id": obj_id,
            "ra": 234.22,
            "dec": -22.33,
            "redshift": 3,
            "transient": False,
            "ra_dis": 2.3,
            "filter_ids": [public_filter.id],
            "passed_at": passed_at,
        },
        token=upload_data_token,
    )
    assert status == 200

    status, data = api("GET", f"candidates/{obj_id}", token=view_only_token)
    assert status == 200
    assert data["data"]["id"] == obj_id
    npt.assert_almost_equal(data["data"]["ra"], 234.22)

    status, data = api(
        "POST",
        "candidates",
        data={
            "id": obj_id,
            "ra": 234.22,
            "dec": -22.33,
            "redshift": 3,
            "transient": False,
            "ra_dis": 2.3,
            "filter_ids": [public_filter.id],
            "passed_at": passed_at,
        },
        token=upload_data_token,
    )
    assert status == 400


def test_candidate_list_sorting_basic(
    annotation_token, view_only_token, public_candidate, public_candidate2
):
    origin = str(uuid.uuid4())
    status, data = api(
        "POST",
        "annotation",
        data={
            "obj_id": public_candidate.id,
            "origin": origin,
            "data": {"numeric_field": 1},
        },
        token=annotation_token,
    )
    assert status == 200

    status, data = api(
        "POST",
        "annotation",
        data={
            "obj_id": public_candidate2.id,
            "origin": origin,
            "data": {"numeric_field": 2},
        },
        token=annotation_token,
    )
    assert status == 200

    # Sort by the numeric field so that public_candidate is returned first,
    # instead of by last_detected_at (which would put public_candidate2 first)
    status, data = api(
        "GET",
        f"candidates/?sortByAnnotationOrigin={origin}&sortByAnnotationKey=numeric_field",
        token=view_only_token,
    )
    assert status == 200
    assert data["data"]["candidates"][0]["id"] == public_candidate.id
    assert data["data"]["candidates"][1]["id"] == public_candidate2.id


def test_candidate_list_sorting_different_origins(
    annotation_token, view_only_token, public_candidate, public_candidate2
):
    origin = str(uuid.uuid4())
    origin2 = str(uuid.uuid4())
    status, data = api(
        "POST",
        "annotation",
        data={
            "obj_id": public_candidate.id,
            "origin": origin,
            "data": {"numeric_field": 1},
        },
        token=annotation_token,
    )
    assert status == 200

    status, data = api(
        "POST",
        "annotation",
        data={
            "obj_id": public_candidate2.id,
            "origin": origin2,
            "data": {"numeric_field": 2},
        },
        token=annotation_token,
    )
    assert status == 200

    # If just sorting on numeric_field, public_candidate should be returned first
    # but since we specify origin2 (which is not the origin for the
    # public_candidate annotation) public_candidate2 is returned first
    status, data = api(
        "GET",
        f"candidates/?sortByAnnotationOrigin={origin2}&sortByAnnotationKey=numeric_field",
        token=view_only_token,
    )
    assert status == 200
    assert data["data"]["candidates"][0]["id"] == public_candidate2.id
    assert data["data"]["candidates"][1]["id"] == public_candidate.id


def test_candidate_list_sorting_hidden_group(
    annotation_token_two_groups,
    view_only_token,
    public_candidate_two_groups,
    public_candidate2,
    public_group2,
):
    # Post an annotation that belongs only to public_group2 (not allowed for view_only_token)
    status, data = api(
        "POST",
        "annotation",
        data={
            "obj_id": public_candidate_two_groups.id,
            "origin": f"{public_group2.id}",
            "data": {"numeric_field": 1},
            "group_ids": [public_group2.id],
        },
        token=annotation_token_two_groups,
    )
    assert status == 200

    # This one belongs to both public groups and is thus visible
    status, data = api(
        "POST",
        "annotation",
        data={
            "obj_id": public_candidate2.id,
            "origin": f"{public_group2.id}",
            "data": {"numeric_field": 2},
        },
        token=annotation_token_two_groups,
    )
    assert status == 200

    # Sort by the numeric field ascending, but since view_only_token does not
    # have access to public_group2, the first annotation above should not be
    # seen in the response
    status, data = api(
        "GET",
        f"candidates/?sortByAnnotationOrigin={public_group2.id}&sortByAnnotationKey=numeric_field",
        token=view_only_token,
    )
    assert status == 200
    assert data["data"]["candidates"][0]["id"] == public_candidate_two_groups.id
    assert data["data"]["candidates"][0]["annotations"] == []
    assert data["data"]["candidates"][1]["id"] == public_candidate2.id


def test_candidate_list_sorting_null_value(
    annotation_token, view_only_token, public_candidate, public_candidate2
):
    origin = str(uuid.uuid4())
    status, data = api(
        "POST",
        "annotation",
        data={
            "obj_id": public_candidate.id,
            "origin": origin,
            "data": {"numeric_field": 1},
        },
        token=annotation_token,
    )
    assert status == 200

    status, data = api(
        "POST",
        "annotation",
        data={
            "obj_id": public_candidate2.id,
            "origin": origin,
            "data": {"some_other_field": 2},
        },
        token=annotation_token,
    )
    assert status == 200

    # The second candidate does not have "numeric_field" in the annotations, and
    # should thus show up after the first candidate, even though it was posted
    # latest
    status, data = api(
        "GET",
        f"candidates/?sortByAnnotationOrigin={origin}&sortByAnnotationKey=numeric_field",
        token=view_only_token,
    )
    assert status == 200
    assert data["data"]["candidates"][0]["id"] == public_candidate.id
    assert data["data"]["candidates"][1]["id"] == public_candidate2.id


def test_candidate_list_filtering_numeric(
    annotation_token, view_only_token, public_candidate, public_candidate2
):
    origin = str(uuid.uuid4())
    status, data = api(
        "POST",
        "annotation",
        data={
            "obj_id": public_candidate.id,
            "origin": origin,
            "data": {"numeric_field": 1},
        },
        token=annotation_token,
    )
    assert status == 200

    status, data = api(
        "POST",
        "annotation",
        data={
            "obj_id": public_candidate2.id,
            "origin": origin,
            "data": {"numeric_field": 2},
        },
        token=annotation_token,
    )
    assert status == 200

    # Filter by the numeric field with max value 1.5 so that only public_candidate
    # is returned
    status, data = api(
        "GET",
        f'candidates/?annotationFilterList={{"origin":"{origin}","key":"numeric_field","min":0, "max":1.5}}',
        token=view_only_token,
    )
    assert status == 200
    assert len(data["data"]["candidates"]) == 1
    assert data["data"]["candidates"][0]["id"] == public_candidate.id


def test_candidate_list_filtering_boolean(
    annotation_token, view_only_token, public_candidate, public_candidate2
):
    origin = str(uuid.uuid4())
    status, data = api(
        "POST",
        "annotation",
        data={
            "obj_id": public_candidate.id,
            "origin": origin,
            "data": {"bool_field": True},
        },
        token=annotation_token,
    )
    assert status == 200

    status, data = api(
        "POST",
        "annotation",
        data={
            "obj_id": public_candidate2.id,
            "origin": origin,
            "data": {"bool_field": False},
        },
        token=annotation_token,
    )
    assert status == 200

    # Filter by the numeric field with value == true so that only public_candidate
    # is returned
    status, data = api(
        "GET",
        f'candidates/?annotationFilterList={{"origin":"{origin}","key":"bool_field","value":"true"}}',
        token=view_only_token,
    )
    assert status == 200
    assert len(data["data"]["candidates"]) == 1
    assert data["data"]["candidates"][0]["id"] == public_candidate.id


def test_candidate_list_filtering_string(
    annotation_token, view_only_token, public_candidate, public_candidate2
):
    origin = str(uuid.uuid4())
    status, data = api(
        "POST",
        "annotation",
        data={
            "obj_id": public_candidate.id,
            "origin": origin,
            "data": {"string_field": "a"},
        },
        token=annotation_token,
    )
    assert status == 200

    status, data = api(
        "POST",
        "annotation",
        data={
            "obj_id": public_candidate2.id,
            "origin": origin,
            "data": {"string_field": "b"},
        },
        token=annotation_token,
    )
    assert status == 200

    # Filter by the numeric field with value == "a" so that only public_candidate
    # is returned
    status, data = api(
        "GET",
        f'candidates/?annotationFilterList={{"origin":"{origin}","key":"string_field","value":"a"}}',
        token=view_only_token,
    )
    assert status == 200
    assert len(data["data"]["candidates"]) == 1
    assert data["data"]["candidates"][0]["id"] == public_candidate.id


def test_candidate_list_classifications(
    upload_data_token,
    taxonomy_token,
    classification_token,
    view_only_token,
    public_filter,
    public_group,
):
    # Post a candidate with a classification, and one without
    obj_id1 = str(uuid.uuid4())
    obj_id2 = str(uuid.uuid4())
    status, data = api(
        "POST",
        "candidates",
        data={
            "id": obj_id1,
            "ra": 234.22,
            "dec": -22.33,
            "redshift": 3,
            "transient": False,
            "ra_dis": 2.3,
            "filter_ids": [public_filter.id],
            "passed_at": str(datetime.datetime.utcnow()),
        },
        token=upload_data_token,
    )
    assert status == 200
    status, data = api(
        "POST",
        "candidates",
        data={
            "id": obj_id2,
            "ra": 234.22,
            "dec": -22.33,
            "redshift": 3,
            "transient": False,
            "ra_dis": 2.3,
            "filter_ids": [public_filter.id],
            "passed_at": str(datetime.datetime.utcnow()),
        },
        token=upload_data_token,
    )
    assert status == 200

    status, data = api(
        "POST", "sources", data={"id": obj_id1}, token=upload_data_token,
    )
    assert status == 200
    status, data = api(
        'POST',
        'taxonomy',
        data={
            'name': "test taxonomy" + str(uuid.uuid4()),
            'hierarchy': taxonomy,
            'group_ids': [public_group.id],
            'provenance': f"tdtax_{__version__}",
            'version': __version__,
            'isLatest': True,
        },
        token=taxonomy_token,
    )
    assert status == 200
    taxonomy_id = data['data']['taxonomy_id']

    status, data = api(
        'POST',
        'classification',
        data={
            'obj_id': obj_id1,
            'classification': 'Algol',
            'taxonomy_id': taxonomy_id,
            'probability': 1.0,
            'group_ids': [public_group.id],
        },
        token=classification_token,
    )
    assert status == 200

    # Filter for candidates with classification 'Algol' - should only get obj_id1 back
    status, data = api(
        "GET",
        "candidates",
        params={"classifications": "Algol", "groupIDs": f"{public_group.id}"},
        token=view_only_token,
    )
    assert status == 200
    assert len(data["data"]["candidates"]) == 1
    assert data["data"]["candidates"][0]["id"] == obj_id1


def test_candidate_list_redshift_range(
    upload_data_token, view_only_token, public_filter, public_group
):
    # Post candidates with different redshifts
    obj_id1 = str(uuid.uuid4())
    obj_id2 = str(uuid.uuid4())
    status, data = api(
        "POST",
        "candidates",
        data={
            "id": obj_id1,
            "ra": 234.22,
            "dec": -22.33,
            "redshift": 0,
            "transient": False,
            "ra_dis": 2.3,
            "filter_ids": [public_filter.id],
            "passed_at": str(datetime.datetime.utcnow()),
        },
        token=upload_data_token,
    )
    assert status == 200
    status, data = api(
        "POST",
        "candidates",
        data={
            "id": obj_id2,
            "ra": 234.22,
            "dec": -22.33,
            "redshift": 1,
            "transient": False,
            "ra_dis": 2.3,
            "filter_ids": [public_filter.id],
            "passed_at": str(datetime.datetime.utcnow()),
        },
        token=upload_data_token,
    )
    assert status == 200

    # Filter for candidates redshift between 0 and 0.5 - should only get obj_id1 back
    status, data = api(
        "GET",
        "candidates",
        params={"redshiftRange": "(0,0.5)", "groupIDs": f"{public_group.id}"},
        token=view_only_token,
    )
    assert status == 200
    assert len(data["data"]["candidates"]) == 1
    assert data["data"]["candidates"][0]["id"] == obj_id1


def test_exclude_by_outdated_annotations(
    annotation_token, view_only_token, public_group, public_candidate, public_candidate2
):
    status, data = api(
        "GET",
        "candidates",
        params={"groupIDs": f"{public_group.id}"},
        token=view_only_token,
    )

    assert status == 200
    num_candidates = len(data["data"]["candidates"])

    origin = str(uuid.uuid4())
    t0 = datetime.datetime.now(datetime.timezone.utc)  # recall when it was created

    # add an annotation from this origin
    status, data = api(
        "POST",
        "annotation",
        data={"obj_id": public_candidate.id, "origin": origin, "data": {'value1': 1}},
        token=annotation_token,
    )
    assert status == 200

    status, data = api(
        "GET",
        "candidates",
        params={"groupIDs": f"{public_group.id}", "annotationExcludeOrigin": origin},
        token=view_only_token,
    )

    assert status == 200
    assert (
        num_candidates == len(data["data"]["candidates"]) + 1
    )  # should have one less candidate

    status, data = api(
        "GET",
        "candidates",
        params={
            "groupIDs": f"{public_group.id}",
            "annotationExcludeOrigin": origin,
            "annotationExcludeOutdatedDate": str(t0 + datetime.timedelta(seconds=3)),
        },
        token=view_only_token,
    )

    assert status == 200
    assert num_candidates == len(
        data["data"]["candidates"]
    )  # should now have all the original candidates
