
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Login - Acme Customer Desk</title>
  <link rel="stylesheet" href="/assets/style.css">
</head>
<body>
<header>
  <h1>Acme Customer Desk</h1>
  <nav>
    <a href="/">Dashboard</a>
    <a href="/customers.jsp">Customers</a>
    <a href="/orders.jsp">Orders</a>
    <a href="/tickets.jsp">Tickets</a>
    <a href="/status.jsp">Status</a>
  </nav>
</header>


<main>

  <div class="notice">Signed in as <strong>support.dan</strong></div>

  <form method="post" action="/login.jsp">
    <label>Username
      <input name="username" autocomplete="username">
    </label>
    <label>Password
      <input name="password" type="password" autocomplete="current-password">
    </label>
    <button type="submit">Sign in</button>
  </form>
</main>
</body>
</html>

