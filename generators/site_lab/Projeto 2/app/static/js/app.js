(() => {
  const searchForm = document.querySelector("#post-search-form");
  const searchInput = document.querySelector("#post-search-input");
  const postList = document.querySelector("#post-list");
  const postDetail = document.querySelector("#post-detail");
  const postComments = document.querySelector("#post-comments");
  const newPostForm = document.querySelector("#new-post-form");
  const newPostAuthor = document.querySelector("#new-post-author");
  const newPostTitle = document.querySelector("#new-post-title");
  const newPostBody = document.querySelector("#new-post-body");
  const newPostTags = document.querySelector("#new-post-tags");
  const newPostStatus = document.querySelector("#new-post-status");
  const commentForm = document.querySelector("#comment-form");
  const commentPostId = document.querySelector("#comment-post-id");
  const commentBody = document.querySelector("#comment-body");
  const commentStatus = document.querySelector("#comment-status");
  const postSort = document.querySelector("#post-sort");
  const postTags = document.querySelector("#post-tags");
  const postPrev = document.querySelector("#post-prev");
  const postNext = document.querySelector("#post-next");
  const postPage = document.querySelector("#post-page");

  if (
    !searchForm || !searchInput || !postList || !postDetail || !postComments ||
    !newPostForm || !newPostAuthor || !newPostTitle || !newPostBody || !newPostTags || !newPostStatus ||
    !commentForm || !postSort || !postTags || !postPrev || !postNext || !postPage
  ) {
    return;
  }

  const requestJson = async (url, options) => {
    const request = window.authFetch || ((target, requestOptions) => window.fetch(target, requestOptions));
    const response = await request(url, options);
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || "Request failed.");
    }
    return payload;
  };

  const requestGraphql = async (query, variables) => {
    const payload = await requestJson("/graphql", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, variables }),
    });
    if (payload.errors && payload.errors.length) {
      throw new Error(payload.errors[0].message || "GraphQL request failed.");
    }
    return payload.data;
  };

  const browseState = { tag: "", sort: "recent", page: 1, perPage: 10 };

  const renderPosts = (posts) => {
    postList.replaceChildren();
    posts.forEach((post) => {
      const article = document.createElement("article");
      article.className = "post-item";
      article.dataset.postId = post.id;

      const heading = document.createElement("h3");
      const openButton = document.createElement("button");
      openButton.className = "post-open";
      openButton.type = "button";
      openButton.dataset.postId = post.id;
      openButton.textContent = post.title;

      const summary = document.createElement("p");
      summary.textContent = post.body;
      const author = document.createElement("p");
      author.className = "post-author";
      author.textContent = `Asked by ${post.author}`;
      heading.append(openButton);
      article.append(heading, author, summary);
      postList.append(article);
    });
  };

  const renderTags = (tags) => {
    postTags.replaceChildren();
    const all = document.createElement("button");
    all.type = "button";
    all.className = "post-tag-filter";
    all.dataset.tag = "";
    all.textContent = "All";
    all.setAttribute("aria-pressed", browseState.tag ? "false" : "true");
    postTags.append(all);
    tags.forEach((tag) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "post-tag-filter";
      button.dataset.tag = tag.name;
      button.textContent = tag.name;
      button.setAttribute("aria-pressed", browseState.tag === tag.name ? "true" : "false");
      postTags.append(button);
    });
  };

  const updatePaging = (count) => {
    postPage.textContent = `Page ${browseState.page}`;
    postPrev.disabled = browseState.page <= 1;
    postNext.disabled = count < browseState.perPage;
  };

  const loadBrowsePosts = async () => {
    const params = new URLSearchParams({
      tag: browseState.tag,
      sort: browseState.sort,
      page: String(browseState.page),
      per_page: String(browseState.perPage),
    });
    const posts = await requestJson(`/api/posts?${params}`);
    renderPosts(posts);
    updatePaging(posts.length);
    renderTags(Array.from(postTags.querySelectorAll(".post-tag-filter")).slice(1).map((button) => ({ name: button.dataset.tag })));
  };

  const loadTags = async () => {
    try {
      renderTags(await requestJson("/api/tags"));
    } catch (_) {
      renderTags([]);
    }
  };

  const runSearch = async () => {
    try {
      if (!searchInput.value) {
        await loadBrowsePosts();
        return;
      }
      const query = new URLSearchParams({ q: searchInput.value });
      renderPosts(await requestJson(`/api/posts/search?${query}`));
    } catch (error) {
      postDetail.textContent = error.message;
    }
  };

  const renderComments = (comments) => {
    postComments.replaceChildren();

    const heading = document.createElement("h2");
    heading.textContent = "Answers";
    postComments.append(heading);

    if (comments.length === 0) {
      const emptyState = document.createElement("p");
      emptyState.textContent = "No answers yet.";
      postComments.append(emptyState);
      return;
    }

    comments.forEach((comment) => {
      const answer = document.createElement("article");
      answer.className = "post-comment";

      const author = document.createElement("h3");
      author.textContent = comment.author;
      const body = document.createElement("p");
      body.textContent = comment.body;
      answer.append(author, body);
      postComments.append(answer);
    });
  };

  const loadComments = async (postId) => {
    const comments = await requestJson(`/api/posts/${encodeURIComponent(postId)}/comments`);
    renderComments(comments);
  };

  const openPost = async (postId) => {
    try {
      const post = await requestJson(`/api/posts/${encodeURIComponent(postId)}`);
      postDetail.replaceChildren();

      const heading = document.createElement("h2");
      heading.textContent = post.title;
      const body = document.createElement("p");
      body.textContent = post.body;
      const author = document.createElement("p");
      author.className = "post-author";
      author.textContent = `Asked by ${post.author}`;
      postDetail.append(heading, author, body);
      commentPostId.value = post.id;
      await loadComments(post.id);
    } catch (error) {
      postDetail.textContent = error.message;
    }
  };

  postList.addEventListener("click", (event) => {
    const button = event.target.closest(".post-open");
    if (button) {
      openPost(button.dataset.postId);
    }
  });

  searchForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    await runSearch();
  });

  let searchTimer;
  searchInput.addEventListener("input", () => {
    window.clearTimeout(searchTimer);
    searchTimer = window.setTimeout(runSearch, 200);
  });

  postSort.addEventListener("change", () => {
    browseState.sort = postSort.value;
    browseState.page = 1;
    searchInput.value = "";
    loadBrowsePosts().catch((error) => { postDetail.textContent = error.message; });
  });

  postTags.addEventListener("click", (event) => {
    const button = event.target.closest(".post-tag-filter");
    if (!button) return;
    browseState.tag = button.dataset.tag || "";
    browseState.page = 1;
    searchInput.value = "";
    loadBrowsePosts().catch((error) => { postDetail.textContent = error.message; });
  });

  postPrev.addEventListener("click", () => {
    if (browseState.page <= 1) return;
    browseState.page -= 1;
    loadBrowsePosts().catch((error) => { postDetail.textContent = error.message; });
  });

  postNext.addEventListener("click", () => {
    if (postNext.disabled) return;
    browseState.page += 1;
    loadBrowsePosts().catch((error) => { postDetail.textContent = error.message; });
  });

  newPostForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    newPostStatus.textContent = "";
    newPostStatus.className = "new-post-status";

    const tags = newPostTags.value ? newPostTags.value.split(",").map((tag) => tag.trim()) : [];
    const mutation = "mutation($t:String!,$b:String!,$a:String,$tags:[String!]){ createPost(title:$t, body:$b, author:$a, tags:$tags){ id title author } }";
    const variables = {
      t: newPostTitle.value,
      b: newPostBody.value,
      a: newPostAuthor.value,
      tags,
    };

    try {
      const data = await requestGraphql(mutation, variables);
      const created = data.createPost;
      newPostForm.reset();
      newPostStatus.textContent = `Post ${created.id} created.`;
      newPostStatus.classList.add("is-success");
      await loadBrowsePosts();
    } catch (error) {
      newPostStatus.textContent = error.message;
      newPostStatus.classList.add("is-error");
    }
  });

  commentForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    commentStatus.textContent = "";
    commentStatus.className = "comment-status";

    try {
      const formData = new FormData(commentForm);
      const comment = await requestJson("/api/comments", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8" },
        body: new URLSearchParams(formData),
      });
      commentBody.value = "";
      commentStatus.textContent = `Comment ${comment.id} posted.`;
      commentStatus.classList.add("is-success");
      await loadComments(commentPostId.value);
    } catch (error) {
      commentStatus.textContent = error.message;
      commentStatus.classList.add("is-error");
    }
  });

  loadTags();
  loadBrowsePosts().catch((error) => {
    postDetail.textContent = error.message;
  });
})();
