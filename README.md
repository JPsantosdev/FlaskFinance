# FlaskFinance

# BR
Este projeto trata-se de uma aplicação web desenvolvida para o curso CS50 ministrado pela universidade de Harvard. Sua construção se baseia em SQL, Python (FLASK), HTML5 e CSS3 puro. Com a aplicação é possível criar contas de usuário, assim como deletá-la. Sua função é simular uma carteira de ações onde um usuário pode comprar e vender ações utilizando o seu saldo dentro do site. Os valores são obtidos por meio de uma API que obtem as siglas das ações e demonstra seu valor. Na tela principal é possível verificar o histórico de ações com as ações compradas e vendidas. Na tela de registro do usuário foi implementado um sistema que define a força de uma senha, exigindo que o usuário insira uma senha com caracteres especiais e ao menos uma letra maiúscula, utilizando-se do REGEX. Por fim, também na página de registro, o sistema certifica-se que o nome inserido pelo usuário não existe no banco de dados SQL, certificando-se que cada usuário seja único.

Uma ferramenta de mudança/lembrança de senha a partir do email do usuário deverá ser implementada futuramente. 

# ENG

This project is a web based aplication developed during Harvard's CS50. It's construction was based on SQL, Python (FLASK), and pure HTML5/CSS3. This application can perform the standard CRUD tasks by allowing the user to register and delete it's own account, purchasing and selling stocks with the website balance, and change it's own password. All the information is stored inside the SQL file. It's objective is to simulate a stocks portfolio, using the YAHOO Finance API to obtain the quotes and stock values from it's Database. In the main screen the user is able to see the stocks purchases and sales of it's account while also being able to change it's password. Inside the user register tab a system that can define the strength of a password was implemented, demanding the user to add a special caracter and a capital letter to the password form using REGEX. Finally, also at the user registration page the system reads the username input and queries through the SQL database, certifying the username does not exist and each username is unique.

A way of changing/reminding the user password by sending an email without the need of being logged in is to be implemented in the near future.
