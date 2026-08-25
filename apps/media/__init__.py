"""Media application namespace.

Uploads currently use Django's MEDIA_ROOT directly; this app owns the URL
namespace so project startup does not depend on a missing package.
"""
