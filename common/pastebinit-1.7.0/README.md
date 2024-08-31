# Using `pastebin.d` files

Add a file in the `~/.pastebin.d`, `/etc/pastebin.d`, or XDG config or data directories with the following format:
```
[pastebin]
basename = domain.name
post_page = api/post.php
paste_regexp = (.*)

[format]
reserved_keyword = pastebin_site_field
custom_keyword = pastebin_site_field

[defaults]
custom_keyword = value
```

# The pastebin section

Under `[pastebin]`, you will want to keep the basic information to identify the pastebin and set it up:

| Setting      | Description
|:-------------|:-----------------------------------------
| basename     | the generic domain name for the pastebin. this domain name should not contain possible subdomains in use.
| post_page    | used to specify a page to which to post data. it is the actual URL of the pastebin's form.
| paste_regexp | used to specify a regular expression to execute on the resulting page after posting. this is useful to deal with special pastebins that don't redirect you to the new paste's URL.
| target_page  | used to compose the paste URL in combination with paste_regexp. the use of `%%s` as a placeholder e.g. for the paste ID is supported.

Furthermore, there are the self-explanatory `https`, `post_format`, and `sizelimit` settings.


# The format section

Under `[format]`, identify the various fields in use in the pastebin you want to set up. Identify any fields used to publish data on the pastebin, and add them to the configuration file.

The `[format]` section expects reserved and custom keywords matched to the real name for the field for the pastebin you are setting up. In other words, the data that a reserved or custom keyword (the left-hand side) refers to will be put in the named field assigned to it (the right-hand side).

A number of reserved keywords can be used, but are optional:

| Keyword  | Description
|:---------|:--------------------------------------
| user     | contains the name of the user.
| content  | contains the data that will be posted.
| title    | contains the title if set at the command line.
| format   | contains the format of the paste, usually used for syntax highlighting.
| private  | makes the paste private if supported.
| expiry   | sets the paste expiration if supported.
| username | contains the pastebin username if required.
| password | contains the pastebin user's password if required.

Any other fields in use for the specific pastebin you are setting up may be added to the `[format]` section using the same syntax.

An easy way to deal with special parameters that need to be passed to the pastebin, such as expiration time for a post, is to assign the pastebin's field name to a variable, and set the correct value for that variable under the `[defaults]` section later, as such:
```
[format]
expiry = expire

[defaults]
expiry = 365
```
Where `expiry` can then be reused as the keyword to retrieve a static value in the `[defaults]` section. See below for an example.

**Note:** This is a bad example now since `expiry` was added as a reserved keyword, but you get the idea.

# The defaults section

The `[defaults]` section is used to set static values for custom fields.

Some pastebins require setting fields such as expiration time for posts, or whether to use cookies. Such values are set using a custom field, followed by the value to give it.

To reuse the example above, statically set a post to expire after 365 days:
```
[defaults]
expiry = 365
```
Here, the value `365` will be assigned to the `expiry` keyword. In the `[format]` section, the value in the `expiry` keyword is applied to the field called `expire`.
