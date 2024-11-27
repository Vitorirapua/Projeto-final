-- Conecte-se ao MySQL usando seu cliente de linha de comando ou uma interface gráfica como MySQL Workbench

-- Primeiro, exclua o banco de dados se ele existir
DROP DATABASE IF EXISTS notepad_db;

-- Crie um novo banco de dados
CREATE DATABASE notepad_db;

-- Selecione o banco de dados que você acabou de criar
USE notepad_db;

CREATE TABLE usuario (
    u_id INT PRIMARY KEY AUTO_INCREMENT,
    u_data TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    u_nome VARCHAR(127) NOT NULL,
    u_nascimento DATE NOT NULL,
    u_email VARCHAR(255) NOT NULL,
    u_senha VARCHAR(63) NOT NULL,
    u_status ENUM ('on', 'off', 'del') DEFAULT 'on'
);

-- Agora, crie a tabela de notas com a coluna 'status'
CREATE TABLE notes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status ENUM('on', 'off') DEFAULT 'on',
    user INT NOT NULL,
    FOREIGN KEY (user) REFERENCES usuario(u_id)
);

-- -------------------------------------- --
-- Insere alguns dados "fake" nas tabelas --
-- -------------------------------------- --

-- Tabela 'usuario'
INSERT INTO usuario (
    u_nome,
    u_nascimento,
    u_email,
    u_senha
) VALUES (
    'Joca da Silva',
    '2000-04-25',
    'jocasilva@email.com',
    SHA1('Senha123') -- Criptografa a senha do usuário
)